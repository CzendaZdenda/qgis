#include "qgsrendererv2widget.h"
#include "qgssymbolv2.h"
#include "qgsvectorlayer.h"
#include <QColorDialog>
#include <QInputDialog>
#include <QMenu>


QgsRendererV2Widget::QgsRendererV2Widget( QgsVectorLayer* layer, QgsStyleV2* style )
    : QWidget(), mLayer( layer ), mStyle( style )
{
}

void QgsRendererV2Widget::contextMenuViewCategories( const QPoint & )
{
  QMenu contextMenu;
  contextMenu.addAction( tr( "Change color" ), this, SLOT( changeSymbolColor( ) ) );
  contextMenu.addAction( tr( "Change transparency" ), this, SLOT( changeSymbolTransparency() ) );
  contextMenu.addAction( tr( "Change output unit" ), this, SLOT( changeSymbolUnit() ) );

  if ( mLayer && mLayer->geometryType() == QGis::Line )
  {
    contextMenu.addAction( tr( "Change width" ), this, SLOT( changeSymbolWidth() ) );
  }
  else if ( mLayer && mLayer->geometryType() == QGis::Point )
  {
    contextMenu.addAction( tr( "Change size" ), this, SLOT( changeSymbolSize() ) );
  }

  contextMenu.exec( QCursor::pos() );
}

void QgsRendererV2Widget::changeSymbolColor()
{
  QList<QgsSymbolV2*> symbolList = selectedSymbols();
  if ( symbolList.size() < 1 )
  {
    return;
  }

  QColor color = QColorDialog::getColor( symbolList.at( 0 )->color(), this );
  if ( color.isValid() )
  {
    QList<QgsSymbolV2*>::iterator symbolIt = symbolList.begin();
    for ( ; symbolIt != symbolList.end(); ++symbolIt )
    {
      ( *symbolIt )->setColor( color );
    }
    refreshSymbolView();
  }
}

void QgsRendererV2Widget::changeSymbolTransparency()
{
  QList<QgsSymbolV2*> symbolList = selectedSymbols();
  if ( symbolList.size() < 1 )
  {
    return;
  }

  bool ok;
  double transparency = QInputDialog::getDouble( this, tr( "Transparency" ), tr( "Change symbol transparency" ), 1 - symbolList.at( 0 )->alpha(), 0.0, 1.0, 1, &ok );
  if ( ok )
  {
    QList<QgsSymbolV2*>::iterator symbolIt = symbolList.begin();
    for ( ; symbolIt != symbolList.end(); ++symbolIt )
    {
      ( *symbolIt )->setAlpha( 1 - transparency );
    }
    refreshSymbolView();
  }
}

void QgsRendererV2Widget::changeSymbolUnit()
{
  QList<QgsSymbolV2*> symbolList = selectedSymbols();
  if ( symbolList.size() < 1 )
  {
    return;
  }

  bool ok;
  int currentUnit = ( symbolList.at( 0 )->outputUnit() == QgsSymbolV2::MM ) ? 0 : 1;
  QString item = QInputDialog::getItem( this, tr( "Symbol unit" ), tr( "Select symbol unit" ), QStringList() << tr( "Millimeter" ) << tr( "Map unit" ), currentUnit, false, &ok );
  if ( ok )
  {
    QgsSymbolV2::OutputUnit unit = ( item.compare( tr( "Millimeter" ) ) == 0 ) ? QgsSymbolV2::MM : QgsSymbolV2::MapUnit;

    QList<QgsSymbolV2*>::iterator symbolIt = symbolList.begin();
    for ( ; symbolIt != symbolList.end(); ++symbolIt )
    {
      ( *symbolIt )->setOutputUnit( unit );
    }
    refreshSymbolView();
  }
}

void QgsRendererV2Widget::changeSymbolWidth()
{
  QList<QgsSymbolV2*> symbolList = selectedSymbols();
  if ( symbolList.size() < 1 )
  {
    return;
  }

  bool ok;
  double width = QInputDialog::getDouble( this, tr( "Width" ), tr( "Change symbol width" ), dynamic_cast<QgsLineSymbolV2*>( symbolList.at( 0 ) )->width(), 0.0, 999999, 1, &ok );
  if ( ok )
  {
    QList<QgsSymbolV2*>::iterator symbolIt = symbolList.begin();
    for ( ; symbolIt != symbolList.end(); ++symbolIt )
    {
      dynamic_cast<QgsLineSymbolV2*>( *symbolIt )->setWidth( width );
    }
    refreshSymbolView();
  }
}

void QgsRendererV2Widget::changeSymbolSize()
{
  QList<QgsSymbolV2*> symbolList = selectedSymbols();
  if ( symbolList.size() < 1 )
  {
    return;
  }

  bool ok;
  double size = QInputDialog::getDouble( this, tr( "Size" ), tr( "Change symbol size" ), dynamic_cast<QgsMarkerSymbolV2*>( symbolList.at( 0 ) )->size(), 0.0, 999999, 1, &ok );
  if ( ok )
  {
    QList<QgsSymbolV2*>::iterator symbolIt = symbolList.begin();
    for ( ; symbolIt != symbolList.end(); ++symbolIt )
    {
      dynamic_cast<QgsMarkerSymbolV2*>( *symbolIt )->setSize( size );
    }
    refreshSymbolView();
  }
}



////////////

//#include <QAction>
#include "qgsfield.h"
#include <QMenu>

QgsRendererV2DataDefinedMenus::QgsRendererV2DataDefinedMenus( QMenu* menu, const QgsFieldMap& flds, QString rotationField, QString sizeScaleField )
    : QObject( menu ), mFlds( flds )
{
  mRotationMenu = new QMenu( tr( "Rotation field" ) );
  mSizeScaleMenu = new QMenu( tr( "Size scale field" ) );

  populateMenu( mRotationMenu, SLOT( rotationFieldSelected() ), rotationField );
  populateMenu( mSizeScaleMenu, SLOT( sizeScaleFieldSelected() ), sizeScaleField );

  menu->addMenu( mRotationMenu );
  menu->addMenu( mSizeScaleMenu );
}

void QgsRendererV2DataDefinedMenus::populateMenu( QMenu* menu, const char* slot, QString fieldName )
{
  QAction* aNo = menu->addAction( tr( "- no field -" ), this, slot );
  aNo->setCheckable( true );
  menu->addSeparator();

  bool hasField = false;
  //const QgsFieldMap& flds = mLayer->pendingFields();
  for ( QgsFieldMap::const_iterator it = mFlds.begin(); it != mFlds.end(); ++it )
  {
    const QgsField& fld = it.value();
    if ( fld.type() == QVariant::Int || fld.type() == QVariant::Double )
    {
      QAction* a = menu->addAction( fld.name(), this, slot );
      a->setCheckable( true );
      if ( fieldName == fld.name() )
      {
        a->setChecked( true );
        hasField = true;
      }
    }
  }

  if ( !hasField )
    aNo->setChecked( true );
}

void QgsRendererV2DataDefinedMenus::rotationFieldSelected()
{
  QObject* s = sender();
  if ( s == NULL )
    return;

  QAction* a = qobject_cast<QAction*>( s );
  if ( a == NULL )
    return;

  QString fldName = a->text();

  updateMenu( mRotationMenu, fldName );

  if ( fldName == tr( "- no field -" ) )
    fldName = QString();

  emit rotationFieldChanged( fldName );
}

void QgsRendererV2DataDefinedMenus::sizeScaleFieldSelected()
{
  QObject* s = sender();
  if ( s == NULL )
    return;

  QAction* a = qobject_cast<QAction*>( s );
  if ( a == NULL )
    return;

  QString fldName = a->text();

  updateMenu( mSizeScaleMenu, fldName );

  if ( fldName == tr( "- no field -" ) )
    fldName = QString();

  emit sizeScaleFieldChanged( fldName );
}

void QgsRendererV2DataDefinedMenus::updateMenu( QMenu* menu, QString fieldName )
{
  foreach( QAction* a, menu->actions() )
  {
    a->setChecked( a->text() == fieldName );
  }
}
