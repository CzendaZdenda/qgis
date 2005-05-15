/***************************************************************************
               QgsCoordinateTransform.cpp  - Coordinate Transforms
                             -------------------
    begin                : Dec 2004
    copyright            : (C) 2004 Tim Sutton
    email                : tim at linfiniti.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
/* $Id$ */
#include <cassert>
#include "qgscoordinatetransform.h"

QgsCoordinateTransform::QgsCoordinateTransform( ) : QObject()

{
  mSourceSRS= new QgsSpatialRefSys();
  mDestSRS = new QgsSpatialRefSys();
}

QgsCoordinateTransform::QgsCoordinateTransform( QString theSourceSRS, QString theDestSRS ) : QObject()

{
  mSourceSRS= new QgsSpatialRefSys(theSourceSRS);
  mDestSRS = new QgsSpatialRefSys(theDestSRS);
  // initialize the coordinate system data structures
  //XXX Who spells initialize initialise?
  //XXX A: Its the queen's english....
  //XXX  : Long live the queen! Lets get on with the initialisation...
  initialise();
}

QgsCoordinateTransform::QgsCoordinateTransform(long theSourceSrid,
    QString theDestWKT,
    QgsSpatialRefSys::SRS_TYPE theSourceSRSType): QObject()
{

  mSourceSRS= new QgsSpatialRefSys(theSourceSrid,theSourceSRSType);
  mDestSRS = new QgsSpatialRefSys(theDestWKT);
  // initialize the coordinate system data structures
  //XXX Who spells initialize initialise?
  //XXX A: Its the queen's english....
  //XXX  : Long live the queen! Lets get on with the initialisation...
  initialise();
}

QgsCoordinateTransform::~QgsCoordinateTransform()
{
  // free the proj objects
  pj_free(mSourceProjection);
  pj_free(mDestinationProjection);
  //delete member poitners
  delete mDestSRS;
  delete mSourceSRS;
}

QgsSpatialRefSys * QgsCoordinateTransform::sourceSRS()
{
  if (mSourceSRS)
  {
    return mSourceSRS;
  }
  else
  {
    return 0;
  }
}

QgsSpatialRefSys * QgsCoordinateTransform::destSRS()
{
  if (mDestSRS)
  {
    return mDestSRS;
  }
  else
  {
    return 0;
  }
}


void QgsCoordinateTransform::setSourceSRS(QgsSpatialRefSys * theSRS)
{
  mSourceSRS = theSRS;
  initialise();
}
void QgsCoordinateTransform::setDestSRS(QgsSpatialRefSys * theSRS)
{
#ifdef QGISDEBUG
  std::cout << "QgsCoordinateTransform::setDestSRS called" << std::endl;
#endif
  mDestSRS = theSRS;
  initialise();
}


void QgsCoordinateTransform::setDestSRSID (long theSRSID)
{
  //!todo Add some logic here to determine if the srsid is a system or user one
#ifdef QGISDEBUG
  std::cout << "QgsCoordinateTransform::setDestSRSID slot called" << std::endl;
#endif
  mDestSRS->createFromSrsId(theSRSID);
  initialise();
}

// XXX This whole function is full of multiple return statements!!!
void QgsCoordinateTransform::initialise()
{

  mInitialisedFlag=false; //guilty until proven innocent...

  // XXX Warning - multiple return paths in this block!!
  if (!mSourceSRS->isValid())
  {
    //mSourceSRS = defaultWkt;
    // Pass through with no projection since we have no idea what the layer
    // coordinates are and projecting them may not be appropriate
    mShortCircuit = true;
    return;
  }

  if (!mDestSRS->isValid())
  {
    //No destination projection is set so we set the default output projection to
    //be the same as input proj. This only happens on the first layer loaded
    //whatever that may be...
    mDestSRS->createFromProj4(mSourceSRS->proj4String());
  }

  //XXX todo overload == operator for QgsSpatialRefSys
  //at the moment srs.parameters contains the whole proj def...soon it wont...
  //if (mSourceSRS->proj4String() == mDestSRS->proj4String())
  if ((*mSourceSRS) == (*mDestSRS))
  {
    // If the source and destination projection are the same, set the short
    // circuit flag (no transform takes place)
    mShortCircuit=true;
    return;
  }
  else
  {
    // Transform must take place
    mShortCircuit=false;
  }
  mProj4DestParms=mDestSRS->proj4String();
  mProj4SrcParms=mSourceSRS->proj4String();


  // init the projections (destination and source)
  mDestinationProjection = pj_init_plus(mProj4DestParms);
  mSourceProjection = pj_init_plus(mProj4SrcParms);

  mInitialisedFlag = true;
  if ( mDestinationProjection == NULL )
  {
    mInitialisedFlag = false;
  }
  if ( mSourceProjection == NULL )
  {
    mInitialisedFlag = false;
  }

  if (mInitialisedFlag)
  {

    std::cout << "------------------------------------------------------------"<< std::endl;
    std::cout << "QgsCoordinateTransform::initialise()" << std::endl;
    std::cout << "The OGR Coordinate transformation for this layer was set to" << std::endl;
    // note overloaded << operator on qgsspatialrefsys cant be used on pointers -
    // so we dereference them like this (*mSourceSRS) (Thanks Lars for pointing that out)
    std::cout << "INPUT: " << std::endl << (*mSourceSRS) << std::endl;
    std::cout << "OUTPUT: " << std::endl << (*mDestSRS)  << std::endl;
    std::cout << "------------------------------------------------------------" << std::endl;
  }
  else
  {
    std::cout << "------------------------------------------------------------"<< std::endl;
    std::cout << "QgsCoordinateTransform::initialise()" << std::endl;
    std::cout << "The OGR Coordinate transformation FAILED TO INITIALISE!" << std::endl;
    std::cout << "------------------------------------------------------------"<< std::endl;
  }
}

//
//
// TRANSFORMERS BELOW THIS POINT .........
//
//
//


QgsPoint QgsCoordinateTransform::transform(const QgsPoint thePoint,TransformDirection direction) const
{
  if (mShortCircuit || !mInitialisedFlag) return thePoint;
  // transform x
  double x = thePoint.x();
  double y = thePoint.y();
  double z = 0.0;
  try
  {

    transformCoords(1, &x, &y, &z, direction );
  }
  catch(QgsCsException &cse)
  {
    //something bad happened....
    // rethrow the exception
    throw cse;
  }
#ifdef QGISDEBUG
  //std::cout << "Point projection...X : " << thePoint.x() << "-->" << x << ", Y: " << thePoint.y() << " -->" << y << std::endl;
#endif
  return QgsPoint(x, y);
}


QgsPoint QgsCoordinateTransform::transform(const double theX, const double theY=0,TransformDirection direction) const
{
  return transform(QgsPoint(theX, theY), direction);
}

void QgsCoordinateTransform::transformInPlace(double& x, double& y, double& z,
    TransformDirection direction) const
{
  if (mShortCircuit || !mInitialisedFlag)
    return;
#ifdef QGISDEBUG
  std::cout << "Using transform in place " << __FILE__ << " " << __LINE__ << std::endl;
#endif
  // transform x
  transformCoords(1, &x, &y, &z, direction );
}

void QgsCoordinateTransform::transformInPlace(std::vector<double>& x,
    std::vector<double>& y, std::vector<double>& z,
    TransformDirection direction) const
{
  if (mShortCircuit || !mInitialisedFlag)
    return;

  assert(x.size() == y.size());

  // Apparently, if one has a std::vector, it is valid to use the
  // address of the first element in the vector as a pointer to an
  // array of the vectors data, and hence easily interface with code
  // that wants C-style arrays.

  transformCoords(x.size(), &x[0], &y[0], &z[0], direction);
}

QgsRect QgsCoordinateTransform::transform(const QgsRect theRect,TransformDirection direction) const
{
  if (mShortCircuit || !mInitialisedFlag) return theRect;
  // transform x
  double x1 = theRect.xMin();
  double y1 = theRect.yMin();
  double x2 = theRect.xMax();
  double y2 = theRect.yMax();

#ifdef QGISDEBUG

  std::cout << "vvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv"<< std::endl;
  std::cout << "Rect  projection..." << std::endl;
  //std::cout << "INPUT: " << std::endl << mSourceSRS << std::endl;
  //std::cout << "PROJ4: " << std::endl << mProj4SrcParms << std::endl;
  //std::cout << "OUTPUT: " << std::endl << mDestSRS  << std::endl;
  //std::cout << "PROJ4: " << std::endl << mProj4DestParms << std::endl;
  std::cout << "INPUT RECT: " << std::endl << x1 << "," << y1 << ":" << x2 << "," << y2 << std::endl;
  std::cout << "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^" << std::endl;
#endif
  // Number of points to reproject------+
  //                                    |
  //                                    V
  try
  {
    double z = 0.0;
    transformCoords(1, &x1, &y1, &z, direction);
    transformCoords(1, &x2, &y2, &z, direction);

  }
  catch(QgsCsException &cse)
  {
    // rethrow the exception
    throw cse;
  }

#ifdef QGISDEBUG
  std::cout << "Rect projection..."
  << "Xmin : "
  << theRect.xMin()
  << "-->" << x1
  << ", Ymin: "
  << theRect.yMin()
  << " -->" << y1
  << "Xmax : "
  << theRect.xMax()
  << "-->" << x2
  << ", Ymax: "
  << theRect.yMax()
  << " -->" << y2
  << std::endl;
#endif
  return QgsRect(x1, y1, x2 , y2);
}
/*
void QgsCoordinateTransform::transformCoords( 
     const int& numPoints, double* x, double* y, double* z,
     TransformDirection direction) const
{
  // use OGR to do the transform
  if(direction == INVERSE)
  {
    // transform from destination (map canvas/project) to layer CS
    inverseTransform->Transform(numPoints, x, y);
  }
  else
  {
    // transform from source layer CS to destination (map canvas/project) 
    forwardTransform->Transform(numPoints, x, y);
 
  }
}
*/
/* XXX THIS IS BASED ON DIRECT USE OF PROJ4
 * XXX preserved for future use if we need it 
 */

void QgsCoordinateTransform::transformCoords( const int& numPoints, double *x, double *y, double *z,TransformDirection direction) const
{
  assert(mProj4DestParms.length() > 0);
  assert(mProj4SrcParms.length() > 0);
#ifdef QGISDEBUG
  //double xorg = x;
  //double yorg = y;
  //std::cout << "[[[[[[Number of points to transform: " << numPoints << "]]]]]]" << std::endl;
#endif
  // use proj4 to do the transform
  QString dir;
  // if the source/destination projection is lat/long, convert the points to radians
  // prior to transforming
  if((pj_is_latlong(mDestinationProjection) && (direction == INVERSE))
      || (pj_is_latlong(mSourceProjection) && (direction == FORWARD)))
  {
    for (int i = 0; i < numPoints; ++i)
    {
      x[i] *= DEG_TO_RAD;
      y[i] *= DEG_TO_RAD;
      z[i] *= DEG_TO_RAD;
    }

  }
  int projResult;
  if(direction == INVERSE)
  {
    /*
    std::cout << "!!!! INVERSE PROJ4 TRANSFORM !!!!" << std::endl; 
    std::cout << "     numPoint: " << numPoints << std::endl; 
    std::cout << "     x       : " << x << std::endl; 
    std::cout << "     y       : " << y << std::endl; 
    */
    projResult = pj_transform(mDestinationProjection, mSourceProjection , numPoints, 0, x, y, z);
    dir = "inverse";
  }
  else
  {
    /*
    std::cout << "!!!! FORWARD PROJ4 TRANSFORM !!!!" << std::endl; 
    std::cout << "     numPoint: " << numPoints << std::endl; 
    std::cout << "     x       : " << x << std::endl; 
    std::cout << "     y       : " << y << std::endl; 
    std::cout << "     z       : " << z << std::endl; 
    */
    assert(mSourceProjection != 0);
    assert(mDestinationProjection !=0);
    projResult = pj_transform(mSourceProjection, mDestinationProjection, numPoints, 0, x, y, z);
    dir = "forward";
  }

  if (projResult != 0)
  {
    //something bad happened....
    QString msg;
    QTextOStream pjErr(&msg);

    pjErr << tr("Failed") << " " << dir << " " << tr("transform of") << x << ", " <<  y
    << pj_strerrno(projResult) << "\n";
    throw  QgsCsException(msg);
  }
  // if the result is lat/long, convert the results from radians back
  // to degrees
  if((pj_is_latlong(mDestinationProjection) && (direction == FORWARD))
      || (pj_is_latlong(mSourceProjection) && (direction == INVERSE)))
  {
    for (int i = 0; i < numPoints; ++i)
    {
      x[i] *= RAD_TO_DEG;
      y[i] *= RAD_TO_DEG;
      z[i] *= RAD_TO_DEG;
    }
  }
#ifdef QGISDEBUG
  // std::cout << "[[[[[[ Projected " << xorg << ", " << yorg << " to "  << x << ", " << y << " ]]]]]]"<< std::endl;
#endif
}
