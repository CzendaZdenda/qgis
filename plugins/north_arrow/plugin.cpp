/***************************************************************************
  plugin.cpp
  Import tool for various worldmap analysis output files
Functions:

-------------------
begin                : Jan 21, 2004
copyright            : (C) 2004 by Tim Sutton
email                : tim@linfiniti.com

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
#include <qpixmap.h>
#include <qpainter.h>
#include <qfont.h>
#include <qpicture.h>
#include <qpointarray.h>
#include <qpaintdevicemetrics.h>

//non qt includes
#include <iostream>
#include <math.h>

//the gui subclass
#include "plugingui.h"

// xpm for creating the toolbar icon
#include "icon.xpm"

#ifdef WIN32
#define QGISEXTERN extern "C" __declspec( dllexport )
#else
#define QGISEXTERN extern "C"
#endif

//
static const char * const ident_ = "$Id$";

static const char * const name_ = "NorthArrow";
static const char * const description_ = "This plugin displays a north arrow overlayed onto the map.";
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
  mRotationInt=0;
  mPlacement=tr("Bottom Left");
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

  pluginMenu->insertItem(QIconSet(icon),"&NorthArrow", this, SLOT(run()));

  menuBarPointer = ((QMainWindow *) qgisMainWindowPointer)->menuBar();

  menuIdInt = qGisInterface->addMenu("&Decorations", pluginMenu);
  // Create the action for tool
  myQActionPointer = new QAction("North Arrow", QIconSet(icon), "&Wmi",0, this, "run");
  // Connect the action to the run
  connect(myQActionPointer, SIGNAL(activated()), this, SLOT(run()));
  //render the arrow each time the map is rendered
  connect(qGisInterface->getMapCanvas(), SIGNAL(renderComplete(QPainter *)), this, SLOT(renderNorthArrow(QPainter *)));
  // Add the icon to the toolbar
  qGisInterface->addToolBarIcon(myQActionPointer);
  // Add the zoom previous tool to the toolbar
  myQActionPointer->addTo(toolBarPointer);
  refreshCanvas();

}
//method defined in interface
void Plugin::help()
{
  //implement me!
}

// Slot called when the buffer menu item is activated
void Plugin::run()
{
  PluginGui *myPluginGui=new PluginGui(qgisMainWindowPointer,"North Arrow",true,0);
  //overides function byt the same name created in .ui
  myPluginGui->setRotation(mRotationInt);
  myPluginGui->setPlacement(mPlacement);
  myPluginGui->setEnabled(mEnable);
  //listen for when the layer has been made so we can draw it
  connect(myPluginGui, SIGNAL(rotationChanged(int)), this, SLOT(rotationChanged(int)));
  connect(myPluginGui, SIGNAL(changePlacement(QString)), this, SLOT(setPlacement(QString)));
  connect(myPluginGui, SIGNAL(enableNorthArrow(bool)), this, SLOT(setEnabled(bool)));
  myPluginGui->show();

}

//! Refresh the map display using the mapcanvas exported via the plugin interface
void Plugin::refreshCanvas()
{
  qGisInterface->getMapCanvas()->refresh();
}

void Plugin::renderNorthArrow(QPainter * theQPainter)
{
#ifdef QGISDEBUG
      std::cout << "Rendering n-arrow"  << std::endl;
#endif
  //Large IF statement controlled by enable check box
  if (mEnable)
  {
    QPixmap myQPixmap; //to store the north arrow image in
#ifdef WIN32
  QString PKGDATAPATH = qApp->applicationDirPath() + "/share/qgis";
#endif
    QString myFileNameQString = QString(PKGDATAPATH) +
                                QString("/images/north_arrows/default.png");
    //std::cout << "Trying to load " << myFileNameQString << std::cout;
    if (myQPixmap.load(myFileNameQString))
    {

      double centerXDouble = myQPixmap.width()/2;
      double centerYDouble = myQPixmap.height()/2;
      //save the current canvas rotation
      theQPainter->save();
      //
      //work out how to shift the image so that it rotates
      //           properly about its center
      //(x cos a + y sin a - x, -x sin a + y cos a - y)
      //
      const double PI = 3.14159265358979323846;
      double myRadiansDouble = (PI/180) * mRotationInt;
      int xShift = static_cast<int>((
                                      (centerXDouble * cos(myRadiansDouble)) +
                                      (centerYDouble * sin(myRadiansDouble))
                                    ) - centerXDouble);
      int yShift = static_cast<int>((
                                      (-centerXDouble * sin(myRadiansDouble)) +
                                      (centerYDouble * cos(myRadiansDouble))
                                    ) - centerYDouble);

      // need width/height of paint device
      QPaintDeviceMetrics myMetrics( theQPainter->device() );
      int myHeight = myMetrics.height();
      int myWidth = myMetrics.width();

#ifdef QGISDEBUG
      std::cout << "Rendering n-arrow at " << mPlacement << std::endl;
#endif
      //Determine placement of label from form combo box
      if (mPlacement==tr("Bottom Left"))
      {
        theQPainter->translate(0,myHeight-myQPixmap.height());
      }
      else if (mPlacement==tr("Top Right"))
      {
        theQPainter->translate(myWidth-myQPixmap.width(),0);
      }
      else if (mPlacement==tr("Bottom Right"))
      {
        theQPainter->translate(myWidth-myQPixmap.width(),
                             myHeight-myQPixmap.height());
      }
      else // defaulting to top left
      {
        //no need to translate for TL corner because we're already at the origin
        theQPainter->translate(0, 0);
      }
      //rotate the canvas by the north arrow rotation amount
      theQPainter->rotate( mRotationInt );
      //Now we can actually do the drawing
      theQPainter->drawPixmap(xShift,yShift,myQPixmap);

      //unrotate the canvase again
      theQPainter->restore();

      //bitBlt ( qGisInterface->getMapCanvas()->canvasPixmap(), 0, 0, &myPainterPixmap, 0, 0, -1 , -1, Qt::CopyROP, false);

    }
    else
    {
      QFont myQFont("time", 32, QFont::Bold);
      theQPainter->setFont(myQFont);
      theQPainter->setPen(Qt::black);
      theQPainter->drawText(10, 20, QString("Pixmap Not Found"));
    }
  }

}
// Unload the plugin by cleaning up the GUI
void Plugin::unload()
{
  // remove the GUI
  menuBarPointer->removeItem(menuIdInt);
  qGisInterface->removeToolBarIcon(myQActionPointer);
  delete myQActionPointer;
}


void Plugin::rotationChanged(int theInt)
{
  mRotationInt = theInt;
  refreshCanvas();
}

//! set placement of north arrow
void Plugin::setPlacement(QString theQString)
{
  mPlacement = theQString;
  refreshCanvas();
}

void Plugin::setEnabled(bool theBool)
{
  mEnable = theBool;
  refreshCanvas();
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
