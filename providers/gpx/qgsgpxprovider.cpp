/***************************************************************************
      qgsgpxprovider.cpp  -  Data provider for GPS eXchange files
                             -------------------
    begin                : 2004-04-14
    copyright            : (C) 2004 by Lars Luthman
    email                : larsl@users.sourceforge.net

    Partly based on qgsdelimitedtextprovider.cpp, (C) 2004 Gary E. Sherman
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

#include <cfloat>
#include <iostream>
#include <limits>
#include <math.h>

#include <qapp.h>
#include <qfile.h>
#include <qtextstream.h>
#include <qstringlist.h>
#include <qdom.h>
#include <qrect.h>

#include "../../src/qgis.h"
#include "../../src/qgsdataprovider.h"
#include "../../src/qgsfeature.h"
#include "../../src/qgsfield.h"
#include "../../src/qgsrect.h"
#include "qgsgpxprovider.h"
#include "gpsdata.h"

#ifdef WIN32
#define QGISEXTERN extern "C" __declspec( dllexport )
#else
#define QGISEXTERN extern "C"
#endif


const char* QgsGPXProvider::attr[] = { "name", "elevation", "symbol", "number",
				       "comment", "description", "source", 
				       "url", "url name" };


QgsGPXProvider::QgsGPXProvider(QString uri) : mDataSourceUri(uri),
					      mMinMaxCacheDirty(true),
					      mEditable(false) {
  
  // assume that it won't work
  mValid = false;
  
  // get the filename and the type parameter from the URI
  int fileNameEnd = uri.find('?');
  if (fileNameEnd == -1 || uri.mid(fileNameEnd + 1, 5) != "type=") {
    std::cerr<<"Bad URI - you need to specify the feature type"<<std::endl;
    return;
  }
  QString typeStr = uri.mid(fileNameEnd + 6);
  mFeatureType = (typeStr == "waypoint" ? WaypointType :
		  (typeStr == "route" ? RouteType : TrackType));
  
  // set up the attributes and the geometry type depending on the feature type
  attributeFields.push_back(QgsField(attr[NameAttr], "text"));
  if (mFeatureType == WaypointType) {
    mGeomType = 1;
    for (int i = 0; i < 8; ++i)
      mAllAttributes.push_back(i);
    attributeFields.push_back(QgsField(attr[EleAttr], "text"));
    attributeFields.push_back(QgsField(attr[SymAttr], "text"));
  }
  else if (mFeatureType == RouteType || mFeatureType == TrackType) {
    mGeomType = 2;
    for (int i = 0; i < 8; ++i)
      mAllAttributes.push_back(i);
    attributeFields.push_back(QgsField(attr[NumAttr], "text"));
  }
  attributeFields.push_back(QgsField(attr[CmtAttr], "text"));
  attributeFields.push_back(QgsField(attr[DscAttr], "text"));
  attributeFields.push_back(QgsField(attr[SrcAttr], "text"));
  attributeFields.push_back(QgsField(attr[URLAttr], "text"));
  attributeFields.push_back(QgsField(attr[URLNameAttr], "text"));
  mFileName = uri.left(fileNameEnd);

  // set the selection rectangle to null
  mSelectionRectangle = 0;
  
  // parse the file
  data = GPSData::getData(mFileName);
  if (data == 0)
    return;
  mValid = true;
  
  // resize the cache matrix
  mMinMaxCache=new double*[attributeFields.size()];
  for(int i=0;i<attributeFields.size();i++) {
    mMinMaxCache[i]=new double[2];
  }
}


QgsGPXProvider::~QgsGPXProvider() {
  for(int i=0;i<fieldCount();i++) {
    delete mMinMaxCache[i];
  }
  delete[] mMinMaxCache;
  GPSData::releaseData(mFileName);
}


/**
 * Get the first feature resulting from a select operation
 * @return QgsFeature
 */
QgsFeature *QgsGPXProvider::getFirstFeature(bool fetchAttributes) {
  mFid = 0;
  return getNextFeature(fetchAttributes);
}


/**
 * Get the next feature resulting from a select operation
 * Return 0 if there are no features in the selection set
 * @return QgsFeature
 */
bool QgsGPXProvider::getNextFeature(QgsFeature &feature, bool fetchAttributes){
  return false;
}


/**
 * Get the next feature resulting from a select operation
 * Return 0 if there are no features in the selection set
 * @return QgsFeature
 */
QgsFeature *QgsGPXProvider::getNextFeature(bool fetchAttributes) {
  QgsFeature* feature = new QgsFeature(-1);
  bool success;
  if (fetchAttributes)
    success = getNextFeature(feature, mAllAttributes);
  else {
    std::list<int> emptyList;
    success = getNextFeature(feature, emptyList);
  }
  if (success)
    return feature;
  delete feature;
  return NULL;
}


QgsFeature * QgsGPXProvider::getNextFeature(std::list<int>& attlist) {
  QgsFeature* feature = new QgsFeature(-1);
  bool success = getNextFeature(feature, attlist);
  if (success)
    return feature;
  delete feature;
  return NULL;
}


bool QgsGPXProvider::getNextFeature(QgsFeature* feature, 
				    std::list<int>& attlist) {
  bool result = false;
  
  std::list<int>::const_iterator iter;
  
  if (mFeatureType == WaypointType) {
    // go through the list of waypoints and return the first one that is in
    // the bounds rectangle
    int maxFid = data->getNumberOfWaypoints();
    
    for (; mFid < maxFid; ++mFid) {
      const Waypoint* wpt;
      wpt = &(data->getWaypoint(mFid));
      if (boundsCheck(wpt->lon, wpt->lat)) {
	feature->setFeatureId(mFid);
	result = true;
	
	// some wkb voodoo
	char* geo = new char[21];
	std::memset(geo, 0, 21);
	geo[0] = endian();
	geo[1] = 1;
	std::memcpy(geo+5, &wpt->lon, sizeof(double));
	std::memcpy(geo+13, &wpt->lat, sizeof(double));
	feature->setGeometry((unsigned char *)geo, sizeof(wkbPoint));
	feature->setValid(true);
	
	// add attributes if they are wanted
	for (iter = attlist.begin(); iter != attlist.end(); ++iter) {
	  switch (*iter) {
	  case 0:
	    feature->addAttribute(attr[NameAttr], wpt->name);
	    break;
	  case 1:
	    if (wpt->ele == -std::numeric_limits<double>::max())
	      feature->addAttribute(attr[EleAttr], "");
	    else
	      feature->addAttribute(attr[EleAttr], QString("%1").arg(wpt->ele));
	    break;
	  case 2:
	    feature->addAttribute(attr[SymAttr], wpt->sym);
	    break;
	  case 3:
	    feature->addAttribute(attr[CmtAttr], wpt->cmt);
	    break;
	  case 4:
	    feature->addAttribute(attr[DscAttr], wpt->desc);
	    break;
	  case 5:
	    feature->addAttribute(attr[SrcAttr], wpt->src);
	    break;
	  case 6:
	    feature->addAttribute(attr[URLAttr], wpt->url);
	    break;
	  case 7:
	    feature->addAttribute(attr[URLNameAttr], wpt->urlname);
	    break;
	  }
	}
	
	++mFid;
	break;
      }
    }
  }
  
  else if (mFeatureType == RouteType) {
    // go through the routes and return the first one that is in the bounds
    // rectangle
    int maxFid = data->getNumberOfRoutes();
    for (; mFid < maxFid; ++mFid) {
      const Route* rte;
      rte = &(data->getRoute(mFid));
      
      if (rte->points.size() == 0)
	continue;
      const Routepoint& rtept(rte->points[0]);
      const QgsRect& b(*mSelectionRectangle);
      if ((rte->xMax >= b.xMin()) && (rte->xMin <= b.xMax()) &&
	  (rte->yMax >= b.yMin()) && (rte->yMin <= b.yMax())) {
	feature->setFeatureId(mFid);
	result = true;
	
	// some wkb voodoo
	int nPoints = rte->points.size();
	char* geo = new char[9 + 16 * nPoints];
	std::memset(geo, 0, 9 + 16 * nPoints);
	geo[0] = endian();
	geo[1] = 2;
	std::memcpy(geo + 5, &nPoints, 4);
	for (int i = 0; i < rte->points.size(); ++i) {
	  std::memcpy(geo + 9 + 16 * i, &rte->points[i].lon, sizeof(double));
	  std::memcpy(geo + 9 + 16 * i + 8, &rte->points[i].lat, sizeof(double));
	}
	feature->setGeometry((unsigned char *)geo, 9 + 16 * nPoints);
	feature->setValid(true);
	
	// add attributes if they are wanted
	for (iter = attlist.begin(); iter != attlist.end(); ++iter) {
	  if (*iter == 0)
	    feature->addAttribute(attr[NameAttr], rte->name);
	  else if (*iter == 1) {
	    if (rte->number == std::numeric_limits<int>::max())
	      feature->addAttribute(attr[NumAttr], "");
	    else
	      feature->addAttribute(attr[NumAttr], QString("%1").arg(rte->number));
	  }
	  else if (*iter == 2)
	    feature->addAttribute(attr[CmtAttr], rte->cmt);
	  else if (*iter == 3)
	    feature->addAttribute(attr[DscAttr], rte->desc);
	  else if (*iter == 4)
	    feature->addAttribute(attr[SrcAttr], rte->src);
	  else if (*iter == 5)
	    feature->addAttribute(attr[URLAttr], rte->url);
	  else if (*iter == 6)
	    feature->addAttribute(attr[URLNameAttr], rte->urlname);
	}
	
	++mFid;
	break;
      }
    }
  }
  
  else if (mFeatureType == TrackType) {
    // go through the tracks and return the first one that is in the bounds
    // rectangle
    int maxFid = data->getNumberOfTracks();
    for (; mFid < maxFid; ++mFid) {
      const Track* trk;
      trk = &(data->getTrack(mFid));
      
      if (trk->segments.size() == 0)
	continue;
      if (trk->segments[0].points.size() == 0)
	continue;
      const Trackpoint& trkpt(trk->segments[0].points[0]);
      const QgsRect& b(*mSelectionRectangle);
      if ((trk->xMax >= b.xMin()) && (trk->xMin <= b.xMax()) &&
	  (trk->yMax >= b.yMin()) && (trk->yMin <= b.yMax())) {
	feature->setFeatureId(mFid);
	result = true;
	
	// some wkb voodoo
	int nPoints = trk->segments[0].points.size();
	char* geo = new char[9 + 16 * nPoints];
	std::memset(geo, 0, 9 + 16 * nPoints);
	geo[0] = endian();
	geo[1] = 2;
	std::memcpy(geo + 5, &nPoints, 4);
	for (int i = 0; i < nPoints; ++i) {
	  std::memcpy(geo + 9 + 16 * i, &trk->segments[0].points[i].lon, sizeof(double));
	  std::memcpy(geo + 9 + 16 * i + 8, &trk->segments[0].points[i].lat, sizeof(double));
	}
	feature->setGeometry((unsigned char *)geo, 9 + 16 * nPoints);
	feature->setValid(true);
	
	// add attributes if they are wanted
	for (iter = attlist.begin(); iter != attlist.end(); ++iter) {
	  if (*iter == 0)
	    feature->addAttribute(attr[NameAttr], trk->name);
	  else if (*iter == 1) {
	    if (trk->number == std::numeric_limits<int>::max())
	      feature->addAttribute(attr[NumAttr], "");
	    else
	      feature->addAttribute(attr[NumAttr], QString("%1").arg(trk->number));
	  }
	  else if (*iter == 2)
	    feature->addAttribute(attr[CmtAttr], trk->cmt);
	  else if (*iter == 3)
	    feature->addAttribute(attr[DscAttr], trk->desc);
	  else if (*iter == 4)
	    feature->addAttribute(attr[SrcAttr], trk->src);
	  else if (*iter == 5)
	    feature->addAttribute(attr[URLAttr], trk->url);
	  else if (*iter == 6)
	    feature->addAttribute(attr[URLNameAttr], trk->urlname);
	}
	
	++mFid;
	break;
      }
    }
  }
  return result;
}


/**
 * Select features based on a bounding rectangle. Features can be retrieved
 * with calls to getFirstFeature and getNextFeature.
 * @param mbr QgsRect containing the extent to use in selecting features
 */
void QgsGPXProvider::select(QgsRect *rect, bool useIntersect) {
  
  // Setting a spatial filter doesn't make much sense since we have to
  // compare each point against the rectangle.
  // We store the rect and use it in getNextFeature to determine if the
  // feature falls in the selection area
  mSelectionRectangle = new QgsRect(*rect);
  // Select implies an upcoming feature read so we reset the data source
  reset();
  // Reset the feature id to 0
  mFid = 0;
}


/**
 * Identify features within the search radius specified by rect
 * @param rect Bounding rectangle of search radius
 * @return std::vector containing QgsFeature objects that intersect rect
 */
std::vector<QgsFeature>& QgsGPXProvider::identify(QgsRect * rect) {
  // reset the data source since we need to be able to read through
  // all features
  reset();
  std::cerr<<"Attempting to identify features falling within "
	    <<rect->stringRep()<<std::endl; 
  // select the features
  select(rect);
  // temporary fix to get this to compile under windows
  std::vector<QgsFeature> features;
  return features;
}


/*
   unsigned char * QgsGPXProvider::getGeometryPointer(OGRFeature *fet){
   unsigned char *gPtr=0;
// get the wkb representation

//geom->exportToWkb((OGRwkbByteOrder) endian(), gPtr);
return gPtr;

}
*/
int QgsGPXProvider::endian() {
  char *chkEndian = new char[4];
  memset(chkEndian, '\0', 4);
  chkEndian[0] = 0xE8;

  int *ce = (int *) chkEndian;
  int retVal;
  if (232 == *ce)
    retVal = NDR;
  else
    retVal = XDR;
  delete[]chkEndian;
  return retVal;
}


// Return the extent of the layer
QgsRect *QgsGPXProvider::extent() {
  return data->getExtent();
}


/** 
 * Return the feature type
 */
int QgsGPXProvider::geometryType() {
  return mGeomType;
}


/** 
 * Return the feature type
 */
long QgsGPXProvider::featureCount() {
  if (mFeatureType == WaypointType)
    return data->getNumberOfWaypoints();
  if (mFeatureType == RouteType)
    return data->getNumberOfRoutes();
  if (mFeatureType == TrackType)
    return data->getNumberOfTracks();
  return 0;
}


/**
 * Return the number of fields
 */
int QgsGPXProvider::fieldCount() {
  return attributeFields.size();
}


std::vector<QgsField>& QgsGPXProvider::fields(){
  return attributeFields;
}


void QgsGPXProvider::reset() {
  // Reset feature id to 0
  mFid = 0;
}


QString QgsGPXProvider::minValue(int position) {
  if (position >= fieldCount()) {
    std::cerr<<"Warning: access requested to invalid position "
	     <<"in QgsGPXProvider::minValue(..)"<<std::endl;
  }
  if (mMinMaxCacheDirty) {
    fillMinMaxCash();
  }
  return QString::number(mMinMaxCache[position][0],'f',2);
}


QString QgsGPXProvider::maxValue(int position) {
  if (position >= fieldCount()) {
    std::cerr<<"Warning: access requested to invalid position "
	     <<"in QgsGPXProvider::maxValue(..)"<<std::endl;
  }
  if (mMinMaxCacheDirty) {
    fillMinMaxCash();
  }
  return QString::number(mMinMaxCache[position][1],'f',2);
}


void QgsGPXProvider::fillMinMaxCash() {
  for(int i=0;i<fieldCount();i++) {
    mMinMaxCache[i][0]=DBL_MAX;
    mMinMaxCache[i][1]=-DBL_MAX;
  }

  QgsFeature f;
  reset();

  getNextFeature(f, true);
  do {
    for(int i=0;i<fieldCount();i++) {
      double value=(f.attributeMap())[i].fieldValue().toDouble();
      if(value<mMinMaxCache[i][0]) {
        mMinMaxCache[i][0]=value;  
      }  
      if(value>mMinMaxCache[i][1]) {
        mMinMaxCache[i][1]=value;  
      }
    }
  } while(getNextFeature(f, true));

  mMinMaxCacheDirty=false;
}


void QgsGPXProvider::setDataSourceUri(QString uri) {
  mDataSourceUri = uri;
}
  

QString QgsGPXProvider::getDataSourceUri() {
  return mDataSourceUri;
}


bool QgsGPXProvider::isValid(){
  return mValid;
}


bool QgsGPXProvider::addFeatures(std::list<QgsFeature*> flist) {
  
  // add all the features
  for (std::list<QgsFeature*>::const_iterator iter = flist.begin(); 
       iter != flist.end(); ++iter) {
    if (!addFeature(*iter))
      return false;
  }
  
  // write back to file
  QDomDocument qdd;
  data->fillDom(qdd);
  QFile file(mFileName);
  if (!file.open(IO_WriteOnly))
    return false;
  QTextStream ostr(&file);
  ostr<<qdd.toString();
  return true;
}


bool QgsGPXProvider::addFeature(QgsFeature* f) {
  unsigned char* geo = f->getGeometry();
  int featureId;
  bool success = false;
  GPSObject* obj = NULL;
  const std::vector<QgsFeatureAttribute>& attrs(f->attributeMap());
  
  // is it a waypoint?
  if (mFeatureType == WaypointType && geo != NULL && geo[1] == 1) {
    
    // add geometry
    Waypoint wpt;
    std::memcpy(&wpt.lon, geo+5, sizeof(double));
    std::memcpy(&wpt.lat, geo+13, sizeof(double));
    
    // add waypoint-specific attributes
    for (int i = 0; i < attrs.size(); ++i) {
      if (attrs[i].fieldName() == attr[EleAttr]) {
	bool eleIsOK;
	double ele = attrs[i].fieldValue().toDouble(&eleIsOK);
	if (eleIsOK)
	  wpt.ele = ele;
      }
      else if (attrs[i].fieldName() == attr[SymAttr]) {
	wpt.sym = attrs[i].fieldValue();
      }
    }
    
    featureId = data->addWaypoint(wpt);
    success = true;
    obj = &(data->getWaypoint(featureId));
  }
  
  // is it a route?
  if (mFeatureType == RouteType && geo != NULL && geo[1] == 2) {

    Route rte;
    
    // reset bounds
    rte.xMin = std::numeric_limits<double>::max();
    rte.xMax = -std::numeric_limits<double>::max();
    rte.yMin = std::numeric_limits<double>::max();
    rte.yMax = -std::numeric_limits<double>::max();

    // add geometry
    int nPoints;
    std::memcpy(&nPoints, geo + 5, 4);
    for (int i = 0; i < nPoints; ++i) {
      double lat, lon;
      std::memcpy(&lon, geo + 9 + 16 * i, sizeof(double));
      std::memcpy(&lat, geo + 9 + 16 * i + 8, sizeof(double));
      Routepoint rtept;
      rtept.lat = lat;
      rtept.lon = lon;
      rte.points.push_back(rtept);
      rte.xMin = rte.xMin < lon ? rte.xMin : lon;
      rte.xMax = rte.xMax > lon ? rte.xMax : lon;
      rte.yMin = rte.yMin < lat ? rte.yMin : lat;
      rte.yMax = rte.yMax > lat ? rte.yMax : lat;
    }
    
    // add route-specific attributes
    for (int i = 0; i < attrs.size(); ++i) {
      if (attrs[i].fieldName() == attr[NumAttr]) {
	bool numIsOK;
	long num = attrs[i].fieldValue().toLong(&numIsOK);
	if (numIsOK)
	  rte.number = num;
      }
    }
    
    featureId = data->addRoute(rte);
    success = true;
    obj = &(data->getRoute(featureId));
  }
  
  // is it a track?
  if (mFeatureType == TrackType && geo != NULL && geo[1] == 2) {

    Track trk;
    TrackSegment trkseg;
    
    // reset bounds
    trk.xMin = std::numeric_limits<double>::max();
    trk.xMax = -std::numeric_limits<double>::max();
    trk.yMin = std::numeric_limits<double>::max();
    trk.yMax = -std::numeric_limits<double>::max();

    // add geometry
    int nPoints;
    std::memcpy(&nPoints, geo + 5, 4);
    for (int i = 0; i < nPoints; ++i) {
      double lat, lon;
      std::memcpy(&lon, geo + 9 + 16 * i, sizeof(double));
      std::memcpy(&lat, geo + 9 + 16 * i + 8, sizeof(double));
      Trackpoint trkpt;
      trkpt.lat = lat;
      trkpt.lon = lon;
      trkseg.points.push_back(trkpt);
      trk.xMin = trk.xMin < lon ? trk.xMin : lon;
      trk.xMax = trk.xMax > lon ? trk.xMax : lon;
      trk.yMin = trk.yMin < lat ? trk.yMin : lat;
      trk.yMax = trk.yMax > lat ? trk.yMax : lat;
    }
    
    // add track-specific attributes
    for (int i = 0; i < attrs.size(); ++i) {
      if (attrs[i].fieldName() == attr[NumAttr]) {
	bool numIsOK;
	long num = attrs[i].fieldValue().toLong(&numIsOK);
	if (numIsOK)
	  trk.number = num;
      }
    }
    
    trk.segments.push_back(trkseg);
    featureId = data->addTrack(trk);
    success = true;
    obj = &(data->getTrack(featureId));
  }
  
  
  // add common attributes
  if (obj) {
    for (int i = 0; i < attrs.size(); ++i) {
      if (attrs[i].fieldName() == attr[NameAttr]) {
	obj->name = attrs[i].fieldValue();
      }
      else if (attrs[i].fieldName() == attr[CmtAttr]) {
	obj->cmt = attrs[i].fieldValue();
      }
      else if (attrs[i].fieldName() == attr[DscAttr]) {
	obj->desc = attrs[i].fieldValue();
      }
      else if (attrs[i].fieldName() == attr[SrcAttr]) {
	obj->src = attrs[i].fieldValue();
      }
      else if (attrs[i].fieldName() == attr[URLAttr]) {
	obj->url = attrs[i].fieldValue();
      }
      else if (attrs[i].fieldName() == attr[URLNameAttr]) {
	obj->urlname = attrs[i].fieldValue();
      }
    }
  }
    
  return success;
}


QString QgsGPXProvider::getDefaultValue(const QString& attr, QgsFeature* f) {
  if (attr == "source")
    return "Digitized in QGIS";
  return "";
}


/** 
 * Check to see if the point is within the selection rectangle
 */
bool QgsGPXProvider::boundsCheck(double x, double y)
{
  bool inBounds = (((x < mSelectionRectangle->xMax()) &&
        (x > mSelectionRectangle->xMin())) &&
      ((y < mSelectionRectangle->yMax()) &&
       (y > mSelectionRectangle->yMin())));
  QString hit = inBounds?"true":"false";
  return inBounds;
}


/**
 * Class factory to return a pointer to a newly created 
 * QgsGPXProvider object
 */
QGISEXTERN QgsGPXProvider * classFactory(const char *uri) {
  return new QgsGPXProvider(uri);
}


/** Required key function (used to map the plugin to a data store type)
*/
QGISEXTERN QString providerKey(){
  return QString("gpx");
}


/**
 * Required description function 
 */
QGISEXTERN QString description(){
  return QString("GPS eXchange format provider");
} 


/**
 * Required isProvider function. Used to determine if this shared library
 * is a data provider plugin
 */
QGISEXTERN bool isProvider(){
  return true;
}


