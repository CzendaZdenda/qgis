/*

 spatialite_c99.c -- FUNCTIONS NEEDING TO BE COMPILED WITH -std=c99

 version 2.3, 2008 October 13

 Author: Sandro Furieri a.furieri@lqt.it

 ------------------------------------------------------------------------------

 Version: MPL 1.1/GPL 2.0/LGPL 2.1

 The contents of this file are subject to the Mozilla Public License Version
 1.1 (the "License"); you may not use this file except in compliance with
 the License. You may obtain a copy of the License at
 http://www.mozilla.org/MPL/

Software distributed under the License is distributed on an "AS IS" basis,
WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
for the specific language governing rights and limitations under the
License.

The Original Code is the SpatiaLite library

The Initial Developer of the Original Code is Alessandro Furieri

Portions created by the Initial Developer are Copyright (C) 2008
the Initial Developer. All Rights Reserved.

Contributor(s):

Alternatively, the contents of this file may be used under the terms of
either the GNU General Public License Version 2 or later (the "GPL"), or
the GNU Lesser General Public License Version 2.1 or later (the "LGPL"),
in which case the provisions of the GPL or the LGPL are applicable instead
of those above. If you wish to allow use of your version of this file only
under the terms of either the GPL or the LGPL, and not to allow others to
use your version of this file under the terms of the MPL, indicate your
decision by deleting the provisions above and replace them with the notice
and other provisions required by the GPL or the LGPL. If you do not delete
the provisions above, a recipient may use your version of this file under
the terms of any one of the MPL, the GPL or the LGPL.

*/

#include <stdlib.h>
#include <math.h>
#include <limits.h>

#include <spatialite/sqlite3ext.h>
#include <spatialite.h>

SPATIALITE_DECLARE sqlite3_int64
math_llabs( sqlite3_int64 value )
{
  /* wrapping the llabs() function */
#ifndef _MSC_VER
  return llabs( value );
#else
  return _abs64( value );
#endif
}

SPATIALITE_DECLARE double
math_round( double value )
{
  /* wrapping the round() function */
#ifndef _MSC_VER
  return ( round( value ) );
#else
  return value >= 0.0 ? floor( value + 0.5 ) : ceil( value - 0.5 );
#endif
}

SPATIALITE_DECLARE sqlite3_int64
min_rowid()
{
  /* returning the LLONG_MIN value */
  return LLONG_MIN;
}