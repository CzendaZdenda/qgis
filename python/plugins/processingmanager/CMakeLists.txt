FILE(GLOB INSTALLER_FILES *.py)
FILE(GLOB UI_FILES dialog.ui panel.ui settings.ui aboutdialog.ui workflowBuilder.ui savedialog.ui)
PYQT4_WRAP_UI(PYUI_FILES ${UI_FILES} ${PYUI_FILES})
PYQT4_ADD_RESOURCES(PYRC_FILES processing.qrc)
SET(INSTALLER_FILES ${INSTALLER_FILES})

ADD_CUSTOM_TARGET(processingplugin ALL DEPENDS ${PYUI_FILES} ${PYRC_FILES})
INSTALL(FILES ${INSTALLER_FILES} ${PYUI_FILES} ${PYRC_FILES} DESTINATION ${QGIS_DATA_DIR}/python/plugins/processingplugin)
