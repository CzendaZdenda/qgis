#include <QtTest>
#include <QObject>
#include <QString>
#include <QStringList>
#include <QObject>
#include <iostream>

#include <QApplication>

#include <qgsvectorlayer.h> //defines QgsFieldMap 
#include <qgsvectorfilewriter.h> //logic for writing shpfiles
#include <qgsfeature.h> //we will need to pass a bunch of these for each rec
#include <qgsgeometry.h> //each feature needs a geometry
#include <qgspoint.h> //we will use point geometry
#include <qgsspatialrefsys.h> //needed for creating a srs
#include <qgsapplication.h> //search path for srs.db
#include <qgsfield.h>
#include <qgis.h> //defines GEOWKT

class TestQgsVectorFileWriter: public QObject
{
  Q_OBJECT;
  private slots:
    void createVectorFile()
    {
      // init QGIS's paths - true means that all path will be inited from prefix
      QString qgisPath = QCoreApplication::applicationDirPath ();
      QgsApplication::setPrefixPath(qgisPath, TRUE);

      std::cout << "Prefix  PATH: " << QgsApplication::prefixPath().toLocal8Bit().data() << std::endl;
      std::cout << "Plugin  PATH: " << QgsApplication::pluginPath().toLocal8Bit().data() << std::endl;
      std::cout << "PkgData PATH: " << QgsApplication::pkgDataPath().toLocal8Bit().data() << std::endl;
      std::cout << "User DB PATH: " << QgsApplication::qgisUserDbFilePath().toLocal8Bit().data() << std::endl;

      QString myEncoding("UTF-8");
      QString myFileName("/tmp/testshp.shp");
      QgsVectorFileWriter::WriterError myError;
      
      // Possible QVariant::Type s
      // QVariant::String
      // QVariant::Int
      // QVariant::Double
      // 
      // Allowed ogr prvider typeNames:
      // Integer
      // Real
      // String
      
      // Constructor for QgsField:
      // QgsField::QgsField(QString name, 
      //                    QVariant::Type type, 
      //                    QString typeName, 
      //                    int len, 
      //                    int prec, 
      //                    QString comment)
      QgsField myField1("Field1",QVariant::String,"String",10,0,"Field 1 comment");
      QgsFieldMap myFields;
      myFields.insert(0, myField1);
      QgsSpatialRefSys mySRS(GEOWKT);
      QgsVectorFileWriter myWriter (myFileName,
          myEncoding,
          myFields,
          QGis::WKBPoint,
          &mySRS);
      //
      // Create a feature
      //
      QgsPoint myPoint(10.0,10.0);
      QgsGeometry * mypGeometry = QgsGeometry::fromPoint(myPoint);
      QgsFeature myFeature;
      myFeature.setGeometry(mypGeometry);
      myFeature.addAttribute(0,"HelloWorld");
      //
      // Write the featyre to the filewriter
      //
      myWriter.addFeature(myFeature);
      myError = myWriter.hasError();
      Q_ASSERT(myError==QgsVectorFileWriter::NoError);
      // other possible outcomes...
      //QgsVectorFileWriter::ErrDriverNotFound:
      //QgsVectorFileWriter::ErrCreateDataSource:
      //QgsVectorFileWriter::ErrCreateLayer:
      delete mypGeometry;
    }
};

QTEST_MAIN(TestQgsVectorFileWriter)
#include "moc_testqgsvectorfilewriter.cxx"

