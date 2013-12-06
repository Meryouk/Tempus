#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
/**
 *   Copyright (C) 2012-2013 IFSTTAR (http://www.ifsttar.fr)
 *   Copyright (C) 2012-2013 Oslandia <infos@oslandia.com>
 *
 *   This library is free software; you can redistribute it and/or
 *   modify it under the terms of the GNU Library General Public
 *   License as published by the Free Software Foundation; either
 *   version 2 of the License, or (at your option) any later version.
 *   
 *   This library is distributed in the hope that it will be useful,
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 *   Library General Public License for more details.
 *   You should have received a copy of the GNU Library General Public
 *   License along with this library; if not, see <http://www.gnu.org/licenses/>.
 */

/***************************************************************************
 IfsttarRoutingDialog
                                 A QGIS plugin
 Get routing informations with various algorithms
                             -------------------
        begin                : 2012-04-12
        copyright            : (C) 2012 by Oslandia
        email                : hugo.mercier@oslandia.com
 ***************************************************************************/
"""

from criterionchooser import CriterionChooser
from stepselector import StepSelector

import os
import pickle
import config

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ui_ifsttarrouting import Ui_IfsttarRoutingDock

from wps_client import *

from qgis.core import *

PREFS_FILE = os.path.expanduser('~/.ifsttarrouting.prefs')

def display_pinpoints( coords, start_letter, style_file, layer_name, canvas ):
    maps = QgsMapLayerRegistry.instance().mapLayers()
    vl = None
    features = {}
    for k,v in maps.items():
        if v.name()[0:len(layer_name)] == layer_name:
            vl = v
            # remove all features
            iter = vl.getFeatures()
            ids = [ f.id() for f in iter ]
            vl.dataProvider().deleteFeatures( ids )
            break

    if vl is None:
        vl = QgsVectorLayer("Point?crs=epsg:2154", layer_name, "memory")
        pr = vl.dataProvider()
        vl.startEditing()
        vl.addAttribute( QgsField( "tag", QVariant.String ) )
        vl.commitChanges()
        vl.updateExtents()
        vl.loadNamedStyle( config.DATA_DIR + "/" + style_file )
        QgsMapLayerRegistry.instance().addMapLayers( [vl] )

    pr = vl.dataProvider()
    i = 0
    for coord in coords:
        fet = QgsFeature()
        pt = QgsPoint( coord[0], coord[1] )
        geo = QgsGeometry.fromPoint( pt )
        fet.setGeometry( geo )
        tag = chr(ord( start_letter )+i)
        fet.setAttributes( [tag] )
        pr.addFeatures( [fet] )
        i = i + 1

    # refresh canvas
    canvas.updateFullExtent()

def update_pinpoints( dock ):
    display_pinpoints( dock.get_coordinates(), 'A', 'style_pinpoints.qml', 'Tempus_pin_points', dock.canvas )

def update_parking( dock ):
    c = dock.get_parking()
    if c == []:
        return
    display_pinpoints( [ c ], 'P', 'style_parking.qml', 'Tempus_private_parking', dock.canvas )

# create the dialog for route queries
class IfsttarRoutingDock(QDockWidget):
    #
    # Set widgets' states from a hash
    #
    def loadState( self, state ):
        self.ui.wpsUrlText.setText( state['wps_url_text'] )
        self.ui.pluginCombo.setCurrentIndex( state['plugin_selected'] )
        
        self.set_steps( state['nsteps'] )
        self.set_selected_criteria( state['criteria'] )
        self.set_coordinates( state['coordinates'] )
        self.set_constraints( state['constraints'] )
        self.set_parking( state['parking'] )
        self.set_pvads( state['pvads'] )

    def loadFromXML( self, xml ):
        pson = to_pson(xml)

        criteria = []
        steps = []
        networks = []
        parking = None
        origin = None
        dep = None
        for child in pson[2:]:
            if child[0] == 'origin':
                origin = child
            elif child[0] == 'departure_constraint':
                dep = child
            elif child[0] == 'parking_location':
                parking = child
            elif child[0] == 'optimizing_criterion':
                criteria.append(int(child[1]))
            elif child[0] == 'allowed_network':
                networks.append(int(child[1]))
            elif child[0] == 'step':
                steps.append(child)
        ttypes = pson[1]['allowed_transport_types']

        def readCoords( n ):
            if n[1].has_key('vertex'):
                # if the point is given by ID
                return None
            return [ float(n[1]['x']), float(n[1]['y']) ]

        if parking:
            parking = readCoords(parking)
            self.set_parking( parking )
        self.set_steps( len(steps) )

        coords = [ readCoords(origin) ]
        constraints = [ [int(dep[1]['type']), dep[1]['date_time'] ] ]
        pvads = []
        for step in steps:
            for p in step[2:]:
                if p[0] == 'destination':
                    coords.append( readCoords(p) )
                elif p[0] == 'constraint':
                    c = p[1]
                    constraints.append( [int(c['type']), c['date_time'] ] )
            pvads.append( step[1]['private_vehicule_at_destination'] == 'true' )

        self.set_selected_criteria( criteria )
        self.set_coordinates( coords )
        self.set_pvads( pvads )
        self.set_constraints( constraints )
        
    #
    # Save widgets' states
    #
    def saveState( self ):
        state = {
            'wps_url_text': self.ui.wpsUrlText.text(),
            'plugin_selected': self.ui.pluginCombo.currentIndex(),
            'nsteps': self.nsteps(),
            'criteria' : self.get_selected_criteria(),
            'coordinates': self.get_coordinates(),
            'constraints': self.get_constraints(),
            'parking' : self.get_parking(),
            'pvads': self.get_pvads(),
            }
        return state

    def __init__(self, canvas):
        QDockWidget.__init__(self)
        self.canvas = canvas
        # Set up the user interface from Designer.
        self.ui = Ui_IfsttarRoutingDock()
        self.ui.setupUi(self)

        self.ui.criterionBox.addWidget( CriterionChooser( self.ui.criterionBox, True ) )

        # set roadmap's header
        self.ui.roadmapTable.setHorizontalHeader(QHeaderView(Qt.Horizontal))
        self.ui.roadmapTable.setHorizontalHeaderLabels( ["", "Direction", "Costs"] )

        # add the Destination chooser
        self.ui.origin.set_canvas( self.canvas )
        dest = StepSelector( self.ui.stepBox, "Destination", False, self, update_pinpoints)
        dest.set_canvas( self.canvas )
        self.ui.stepBox.addWidget( dest )

        # set pin points updater
        self.ui.origin.updateCallback = update_pinpoints
        self.ui.origin.dock = self

        # add the private parking chooser
        self.parkingChooser = StepSelector( self.ui.queryPage, "Private parking location", True )
        self.parkingChooser.set_canvas( self.canvas )
        self.ui.parkingLayout.addWidget( self.parkingChooser )

        # set parking location updater
        self.parkingChooser.updateCallback = update_parking
        self.parkingChooser.dock = self

        # preferences is an object used to store user preferences
        if os.path.exists( PREFS_FILE ):
            f = open( PREFS_FILE, 'r' )
            self.prefs = pickle.load( f )
            self.loadState( self.prefs )
        else:
            self.prefs = {}

    def updateLayers( self ):
        "Update pinpoints and parking layers"
        update_pinpoints( self )
        update_parking( self )

    def closeEvent( self, event ):
        self.prefs = self.saveState()
        f = open( PREFS_FILE, 'w+' )
        pickle.dump( self.prefs, f )
        event.accept()

    def get_selected_criteria( self ):
        s = []
        for c in range( 0, self.ui.criterionBox.count() ):
            s.append( self.ui.criterionBox.itemAt( c ).widget().selected() )
        return s

    def set_selected_criteria( self, sel ):
        c = self.ui.criterionBox.count()
        for i in range(0, c-1):
            self.ui.criterionBox.itemAt(1).widget().onRemove()
        for i in range(0, len(sel)-1 ):
            self.ui.criterionBox.itemAt(0).widget().onAdd()

        i = 0
        for selected in sel:
            self.ui.criterionBox.itemAt(i).widget().set_selection( selected )
            i += 1

    # get coordinates of all steps
    def get_coordinates( self ):
        coords = [ self.ui.origin.get_coordinates() ]
        n = self.nsteps()
        for i in range(0, n):
            w = self.ui.stepBox.itemAt(i).widget()
            coord = w.get_coordinates()
            coords.append( coord )
        return coords

    def nsteps( self ):
        return self.ui.stepBox.count()

    def set_coordinates( self, coords ):
        self.ui.origin.set_coordinates( coords[0] )
        n = 0
        for coord in coords[1:]:
            if self.ui.stepBox.count() > n:
                self.ui.stepBox.itemAt( n ).widget().set_coordinates( coord )
            n += 1

    def get_constraints( self ):
        c = [ [self.ui.origin.get_constraint_type(), self.ui.origin.get_constraint()] ]
        n = self.nsteps()
        for i in range(0, n):
            t = self.ui.stepBox.itemAt( i ).widget().get_constraint_type()
            cs = self.ui.stepBox.itemAt( i ).widget().get_constraint()
            c.append( [ t, cs ] )
        return c

    def set_constraints( self, constraints ):
        self.ui.origin.set_constraint_type( constraints[0][0] )
        self.ui.origin.set_constraint( constraints[0][1] )
        i = 0
        for constraint in constraints[1:]:
            self.ui.stepBox.itemAt( i ).widget().set_constraint_type( constraint[0] )
            self.ui.stepBox.itemAt( i ).widget().set_constraint( constraint[1] )
            i += 1

    def get_pvads( self ):
        pvads = []
        n = self.nsteps()
        for i in range(0, n):
            pvads.append( self.ui.stepBox.itemAt( i ).widget().get_pvad() )
        return pvads

    def set_pvads( self, pvads ):
        i = 0
        for pvad in pvads:
            self.ui.stepBox.itemAt( i ).widget().set_pvad( pvad )
            i += 1

    def selected_networks( self ):
        s = []
        model = self.ui.networkList.model()
        n = model.rowCount()
        for i in range(0, n):
            v = model.data( model.index(i,0), Qt.CheckStateRole )
            if v == Qt.Checked:
                s.append( i )
        return s

    def selected_transports( self ):
        s = []
        model = self.ui.transportList.model()
        n = model.rowCount()
        for i in range(0, n):
            v = model.data( model.index(i,0), Qt.CheckStateRole )
            if v == Qt.Checked:
                s.append( i )
        return s

    def set_selected_networks( self, sel ):
        model = self.ui.networkList.model()
        n = model.rowCount()
        for i in range(0, n):
            if i in sel:
                q = Qt.Checked
            else:
                q = Qt.Unchecked
            model.setData( model.index(i,0), q, Qt.CheckStateRole )

    def set_selected_transports( self, sel ):
        model = self.ui.transportList.model()
        n = model.rowCount()
        for i in range(0, n):
            if i in sel:
                q = Qt.Checked
            else:
                q = Qt.Unchecked
            model.setData( model.index(i,0), q, Qt.CheckStateRole )

    def get_parking( self ):
        [x,y] = self.parkingChooser.get_coordinates()
        if x < 0.001:
            return []
        return [x,y]

    def set_parking( self, xy ):
        self.parkingChooser.set_coordinates( xy )

    def set_steps( self, nsteps ):
        # first remove all intermediary steps
        c = self.ui.stepBox.count()
        # remove from idx 1 to N-1 (skip destination)
        for i in range(1, c):
            self.ui.stepBox.itemAt(0).widget().onRemove()
        
        for i in range(0, nsteps-1):
            self.ui.stepBox.itemAt(0).widget().onAdd()

