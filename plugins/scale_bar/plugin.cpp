/***************************************************************************
  plugin.cpp 
  Plugin to draw scale bar on map
Functions:

-------------------
begin                : Jun 1, 2004
copyright            : (C) 2004 by Peter Brewer
email                : sbr00pwb@users.sourceforge.net

 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
/*  $Id$ */

// includes

#include <qgisapp.h>
#include <qgsmaplayer.h>
#include <qgsrasterlayer.h>
#include "plugin.h"


#include <qtoolbar.h>
#include <qmenubar.h>
#include <qmessagebox.h>
#include <qpopupmenu.h>
#include <qlineedit.h>
#include <qaction.h>
#include <qapplication.h>
#include <qcursor.h>
#include <qpen.h> 
#include <qgspoint.h>
#include <qpointarray.h>
#include <qgscoordinatetransform.h>
#include <qstring.h> 
#include <qfontmetrics.h> 
#include <qfont.h> 
#include <qpaintdevicemetrics.h> 
#include <qspinbox.h> 
#include <qcolor.h> 
#include <qcolordialog.h> 

//non qt includes
#include <iostream>

//the gui subclass
#include "plugingui.h"

// xpm for creating the toolbar icon
#include "icon.xpm"
// 
#ifdef WIN32
#define QGISEXTERN extern "C" __declspec( dllexport )
#else
#define QGISEXTERN extern "C"
#endif

static const char * const ident_ = "$Id$";

static const char * const name_ = "ScaleBar";
static const char * const description_ = "Plugin to draw scale bar on map";
static const char * const version_ = "Version 0.1";
static const QgisPlugin::PLUGINTYPE type_ = QgisPlugin::UI;


/**
 * Constructor for the plugin. The plugin is passed a pointer to the main app
 * and an interface object that provides access to exposed functions in QGIS.
 * @param qgis Pointer to the QGIS main window
 * @param _qI Pointer to the QGIS interface object
 */
Plugin::Plugin(QgisApp * theQGisApp, QgisIface * theQgisInterFace):
qgisMainWindowPointer(theQGisApp), 
    qGisInterface(theQgisInterFace),
QgisPlugin(name_,description_,version_,type_)
{
  mPreferredSize = 100;
  mPlacement = "Top Left";
  mStyle = "Tick Down";
}

Plugin::~Plugin()
{

}

/*
 * Initialize the GUI interface for the plugin 
 */
void Plugin::initGui()
{
  // add a menu with 2 items
  QPopupMenu *pluginMenu = new QPopupMenu(qgisMainWindowPointer);

  pluginMenu->insertItem(QIconSet(icon),"&ScaleBar", this, SLOT(run()));

  menuBarPointer = ((QMainWindow *) qgisMainWindowPointer)->menuBar();

  menuIdInt = qGisInterface->addMenu("&Scale Bar", pluginMenu);
  // Create the action for tool
  QAction *myQActionPointer = new QAction("Scale Bar", QIconSet(icon), "&Wmi",0, this, "run");
  // Connect the action to the run
  connect(myQActionPointer, SIGNAL(activated()), this, SLOT(run()));
  //render the scale bar each time the map is rendered
  connect(qGisInterface->getMapCanvas(), SIGNAL(renderComplete(QPainter *)), this, SLOT(renderScaleBar(QPainter *)));
  // Add the toolbar
  toolBarPointer = new QToolBar((QMainWindow *) qgisMainWindowPointer, "Scale Bar");
  toolBarPointer->setLabel("Scale Bar");
  // Add the zoom previous tool to the toolbar
  myQActionPointer->addTo(toolBarPointer);

}


//method defined in interface
void Plugin::help()
{
  //implement me!
}

// Slot called when the  menu item is activated
void Plugin::run()
{
  PluginGui *myPluginGui=new PluginGui(qgisMainWindowPointer,"Scale Bar",true,0);
  myPluginGui->setPreferredSize(mPreferredSize);
  myPluginGui->setSnapping(mSnapping);
  myPluginGui->setPlacement(mPlacement);
  myPluginGui->setEnabled(mEnabled);
  myPluginGui->setStyle(mStyle);
  myPluginGui->setColour(mColour);
  connect(myPluginGui, SIGNAL(changePreferredSize(int)), this, SLOT(setPreferredSize(int)));
  connect(myPluginGui, SIGNAL(changeSnapping(bool)), this, SLOT(setSnapping(bool)));
  connect(myPluginGui, SIGNAL(changePlacement(QString)), this, SLOT(setPlacement(QString)));
  connect(myPluginGui, SIGNAL(changeEnabled(bool)), this, SLOT(setEnabled(bool)));
  connect(myPluginGui, SIGNAL(changeStyle(QString)), this, SLOT(setStyle(QString)));
  connect(myPluginGui, SIGNAL(changeColour(QColor)), this, SLOT(setColour(QColor)));
  connect(myPluginGui, SIGNAL(refreshCanvas()), this, SLOT(refreshCanvas()));
  myPluginGui->show();

  //set the map units in the spin box
  int myUnits=qGisInterface->getMapCanvas()->mapUnits();
  switch (myUnits)
  {
      case 0: myPluginGui->spnSize->setSuffix(tr(" metres")); break;
      case 1: myPluginGui->spnSize->setSuffix(tr(" feet")); break;
      case 2: myPluginGui->spnSize->setSuffix(tr(" degrees")); break;
      default: std::cout << "Error: not picked up map units - actual value = " << myUnits << std::endl; 
  }; 
}


void Plugin::refreshCanvas()
{
  qGisInterface->getMapCanvas()->refresh();
}



// Actual drawing of Scale Bar
void Plugin::renderScaleBar(QPainter * theQPainter)
{
  int myBufferSize=1; //softcode this later
  // Exit if there are no layers loaded otherwise QGIS will freeze
  int myLayerCount=qGisInterface->getMapCanvas()->layerCount();          
  if (!myLayerCount) return;

  //Large if statement which determines whether to render the scale bar
  if (mEnabled)
  { 
    // Hard coded sizes
    int myMajorTickSize=8;
    int myTextOffsetX=3;
    int myTextOffsetY=3;
    double myActualSize=mPreferredSize;
    int myMargin=20;

    //Get canvas dimensions
    QPaintDeviceMetrics myMetrics( theQPainter->device() );
    int myCanvasHeight = myMetrics.height();
    int myCanvasWidth = myMetrics.width();

    //Get map units per pixel   
    double myMuppDouble=qGisInterface->getMapCanvas()->mupp();   

    //Calculate size of scale bar for preferred number of map units
    double myScaleBarWidth = mPreferredSize / myMuppDouble;

    //If scale bar is very small reset to 1/4 of the canvas wide
    if (myScaleBarWidth < 30)
    {
      myScaleBarWidth = myMuppDouble * (myCanvasWidth/4);
      myActualSize = myScaleBarWidth * myMuppDouble;
    };

    //if scale bar is more than half the canvas wide keep halving until not
    while (myScaleBarWidth > myCanvasWidth/2)
    {
      myScaleBarWidth = myScaleBarWidth /2;
    };
    myActualSize = myScaleBarWidth * myMuppDouble;

    // snap to integer < 10 times power of 10
    if (mSnapping) {
      int myPowerOf10 = pow(10, int(log(myActualSize) / log(10)));
      myActualSize = round(myActualSize / myPowerOf10) * myPowerOf10;
      myScaleBarWidth = myActualSize / myMuppDouble;
    }

    //Get type of map units and set scale bar unit label text
    int myMapUnits=qGisInterface->getMapCanvas()->mapUnits();
    QString myScaleBarUnitLabel;
    switch (myMapUnits)
    {
        case 0: myScaleBarUnitLabel=tr(" metres"); break;
        case 1: myScaleBarUnitLabel=tr(" feet"); break;
        case 2: myScaleBarUnitLabel=tr(" degrees"); break;
        default: std::cout << "Error: not picked up map units - actual value = " << myMapUnits << std::endl; 
    };  

    //Set font and calculate width of unit label
    int myFontSize = 10; //we use this later for buffering
    QFont myFont( "helvetica", myFontSize );
    theQPainter->setFont(myFont);
    QFontMetrics myFontMetrics( myFont );
    double myFontWidth = myFontMetrics.width( myScaleBarUnitLabel );
    double myFontHeight = myFontMetrics.height();

    //Set the maximum label
    QString myScaleBarMaxLabel=QString::number(myActualSize);

    //Calculate total width of scale bar and label
    double myTotalScaleBarWidth = myScaleBarWidth + myFontWidth;

    //determine the origin of scale bar depending on placement selected
    int myOriginX=myMargin;
    int myOriginY=myMargin;
    if (mPlacement==tr("Top Left"))
    { 
      myOriginX=myMargin;
      myOriginY=myMargin;
    }
    else if (mPlacement==tr("Bottom Left"))
    {
      myOriginX=myMargin;
      myOriginY=myCanvasHeight - myMargin; 
    }
    else if (mPlacement==tr("Top Right"))
    {
      myOriginX=myCanvasWidth - ((int) myTotalScaleBarWidth) - myMargin;
      myOriginY=myMargin;
    }
    else if (mPlacement==tr("Bottom Right"))
    {
      myOriginX=myCanvasWidth - ((int) myTotalScaleBarWidth) - myMargin;
      myOriginY=myCanvasHeight - myMargin;
    }
    else
    {
      std::cout << "Unable to determine where to put scale bar so defaulting to top left" << std::endl;
    }

    //Set pen to draw with
    //Perhaps enable colour selection in future?
    QPen pen( mColour, 2 );             
    theQPainter->setPen( pen ); 

    //Cast myScaleBarWidth to int for drawing
    int myScaleBarWidthInt = (int) myScaleBarWidth;

    //Create array of vertices for scale bar depending on style    
    if (mStyle==tr("Tick Down"))
    {    
      QPointArray myTickDownArray(4);
      myTickDownArray.putPoints(0,4,
              myOriginX                    , (myOriginY + myMajorTickSize) ,  
              myOriginX                    ,  myOriginY                    ,
              (myScaleBarWidthInt + myOriginX),  myOriginY                    ,
              (myScaleBarWidthInt + myOriginX), (myOriginY + myMajorTickSize)
              ); 	 
      theQPainter->drawPolyline(myTickDownArray);    
    }
    else if (mStyle==tr("Tick Up"))
    {
      QPointArray myTickUpArray(4);
      myTickUpArray.putPoints(0,4,
              myOriginX                    ,  myOriginY                    ,  
              myOriginX                    ,  myOriginY + myMajorTickSize  ,
              (myScaleBarWidthInt + myOriginX),  myOriginY + myMajorTickSize  ,
              (myScaleBarWidthInt + myOriginX),  myOriginY
              ); 
      theQPainter->drawPolyline(myTickUpArray);
    }	    
    else if (mStyle==tr("Bar"))
    {
      QPointArray myBarArray(2);
      myBarArray.putPoints(0,2,
              myOriginX                    ,  (myOriginY + (myMajorTickSize/2)),  
              (myScaleBarWidthInt + myOriginX),  (myOriginY + (myMajorTickSize/2))
              ); 
      theQPainter->drawPolyline(myBarArray);
    }	     
    else if (mStyle==tr("Box"))
    {
      QPointArray myBoxArray(5);
      myBoxArray.putPoints(0,5,
              myOriginX                    ,  myOriginY,  
              (myScaleBarWidthInt + myOriginX),  myOriginY,
              (myScaleBarWidthInt + myOriginX), (myOriginY+myMajorTickSize),
              myOriginX                    , (myOriginY+myMajorTickSize),
              myOriginX                    ,  myOriginY
              ); 
      theQPainter->drawPolyline(myBoxArray);
    }	    

    //Do actual drawing of scale bar

    //
    //Do drawing of scale bar text
    //

    QColor myBackColor = Qt::white;
    QColor myForeColor = Qt::black;

    //Draw the minimum label buffer
    theQPainter->setPen( myBackColor );
    myFontWidth = myFontMetrics.width( "0" );
    myFontHeight = myFontMetrics.height();

    for (int i = 0-myBufferSize; i <= myBufferSize; i++)
    {
      for (int j = 0-myBufferSize; j <= myBufferSize; j++) 
      {
        theQPainter->drawText( i +(myOriginX-(myFontWidth/2)), 
                              j + (myOriginY-(myFontHeight/4)), 
                              "0");
      }
    }

    //Draw minimum label
    theQPainter->setPen( myForeColor );

    theQPainter->drawText(
            (myOriginX-(myFontWidth/2)),(myOriginY-(myFontHeight/4)),
            "0"
            );    
    
    //
    //Draw maximum label      
    //
    theQPainter->setPen( myBackColor );
    myFontWidth = myFontMetrics.width( myScaleBarMaxLabel );
    myFontHeight = myFontMetrics.height();  
    //first the buffer
    for (int i = 0-myBufferSize; i <= myBufferSize; i++)
    {
      for (int j = 0-myBufferSize; j <= myBufferSize; j++) 
      {
        theQPainter->drawText( i + (myOriginX+myScaleBarWidthInt-(myFontWidth/2)), 
                              j + (myOriginY-(myFontHeight/4)), 
                              myScaleBarMaxLabel);
      }
    }
    //then the text itself
    theQPainter->setPen( myForeColor );
    theQPainter->drawText(
            (myOriginX+myScaleBarWidthInt-(myFontWidth/2)),(myOriginY-(myFontHeight/4)),
            myScaleBarMaxLabel
            );
    
    //
    //Draw unit label
    //
    theQPainter->setPen( myBackColor );
    myFontWidth = myFontMetrics.width( myScaleBarUnitLabel );
    myFontHeight = myFontMetrics.height();
    //first the buffer
    for (int i = 0-myBufferSize; i <= myBufferSize; i++)
    {
      for (int j = 0-myBufferSize; j <= myBufferSize; j++) 
      {
        theQPainter->drawText( i + (myOriginX+myScaleBarWidthInt+myTextOffsetX), 
                              j + (myOriginY+myMajorTickSize), 
                              myScaleBarUnitLabel);
      }
    }
    //then the text itself
    theQPainter->setPen( myForeColor );
    theQPainter->drawText(
            (myOriginX+myScaleBarWidthInt+myTextOffsetX),(myOriginY+myMajorTickSize),
            myScaleBarUnitLabel
            );
  }
}



// Unload the plugin by cleaning up the GUI
void Plugin::unload()
{
  // remove the GUI
  menuBarPointer->removeItem(menuIdInt);
  delete toolBarPointer;
}

//! set placement of scale bar
void Plugin::setPlacement(QString theQString)
{
  mPlacement = theQString;
}

//! set preferred size of scale bar
void Plugin::setPreferredSize(int thePreferredSize)
{
  mPreferredSize = thePreferredSize;
}

//! set whether the scale bar length should snap to the closes A*10^B
void Plugin::setSnapping(bool theSnapping)
{
  mSnapping = theSnapping;
}

//! set scale bar enable
void Plugin::setEnabled(bool theBool)
{
  mEnabled = theBool;
}
//! set scale bar enable
void Plugin::setStyle(QString theStyleQString)
{
  mStyle = theStyleQString;
}  
//! set the scale bar colour
void Plugin::setColour(QColor theQColor)
{
  mColour = theQColor;
}


/** 
 * Required extern functions needed  for every plugin 
 * These functions can be called prior to creating an instance
 * of the plugin class
 */
// Class factory to return a new instance of the plugin class
QGISEXTERN QgisPlugin * classFactory(QgisApp * theQGisAppPointer, QgisIface * theQgisInterfacePointer)
{
  return new Plugin(theQGisAppPointer, theQgisInterfacePointer);
}

// Return the name of the plugin - note that we do not user class members as
// the class may not yet be insantiated when this method is called.
QGISEXTERN QString name()
{
  return name_;
}

// Return the description
QGISEXTERN QString description()
{
  return description_;
}

// Return the type (either UI or MapLayer plugin)
QGISEXTERN int type()
{
  return type_;
}

// Return the version number for the plugin
QGISEXTERN QString version()
{
  return version_;
}

// Delete ourself
QGISEXTERN void unload(QgisPlugin * thePluginPointer)
{
  delete thePluginPointer;
}
