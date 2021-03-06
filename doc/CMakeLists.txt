# include doxygen documentation
SET (WITH_APIDOC FALSE CACHE BOOL "Determines whether the QGIS API doxygen documentation should be built")

# include doxygen documentation
SET (WITH_TXT2TAGS_PDF FALSE CACHE BOOL "Determines whether PDF should be generate for the txt2tags documentation")

INCLUDE(Txt2Tags)
FIND_TXT2TAGS()

IF(TXT2TAGS_EXECUTABLE)
  ADD_TXT2TAGS_FILES(QGIS_DOC_FILES INSTALL.t2t CODING.t2t changelog.t2t)
  IF(WITH_TXT2TAGS_PDF)
    ADD_TXT2TAGS_PDFS(QGIS_DOC_FILES INSTALL.t2t CODING.t2t changelog.t2t)
  ENDIF(WITH_TXT2TAGS_PDF)
  ADD_CUSTOM_TARGET (t2tdoc ALL DEPENDS ${QGIS_DOC_FILES})
ELSE(TXT2TAGS_EXECUTABLE)
  SET(QGIS_DOC_FILES
    ${CMAKE_SOURCE_DIR}/INSTALL 
    ${CMAKE_SOURCE_DIR}/CODING
  )
ENDIF(TXT2TAGS_EXECUTABLE)

SET(QGIS_DOC_FILES ${QGIS_DOC_FILES} index.html changelog.html favicon.ico style.css AUTHORS CONTRIBUTORS SPONSORS DONORS TRANSLATORS)

INSTALL(FILES ${QGIS_DOC_FILES} DESTINATION ${QGIS_DATA_DIR}/doc)
INSTALL(FILES images/qgis_new_80pct.png DESTINATION ${QGIS_DATA_DIR}/doc/images)

IF(WITH_APIDOC)
  FIND_PACKAGE(Doxygen)
  IF(DOXYGEN_FOUND)
    CONFIGURE_FILE(${CMAKE_SOURCE_DIR}/cmake_templates/Doxyfile.in ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile @ONLY)
    ADD_CUSTOM_TARGET(apidoc ALL
            COMMAND ${DOXYGEN_EXECUTABLE} ${CMAKE_CURRENT_BINARY_DIR}/Doxyfile
            WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
            DEPENDS qgis_core qgis_gui qgis_analysis
            COMMENT "Generating API documentation" VERBATIM)
    INSTALL(DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/api/html/ DESTINATION ${QGIS_DATA_DIR}/doc/api)
  ELSE(DOXYGEN_FOUND)
    MESSAGE(STATUS "QGIS api documentation not built - Doxygen not found")
  ENDIF(DOXYGEN_FOUND)
ENDIF(WITH_APIDOC)

#SUBDIRS (images plugins install_guide)
