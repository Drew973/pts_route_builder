# -*- coding: utf-8 -*-
import os
from PyQt4 import QtGui, uic
from qgis.PyQt.QtCore import pyqtSignal,QDate,Qt

import route
from qgis.utils import iface
from PyQt4.QtGui import QMenu

from qgis.core import QgsCoordinateReferenceSystem,QgsCoordinateTransform,QgsProject
from qgis.gui import QgsFieldProxyModel

from qgis.PyQt.QtCore import QSettings
settings=QSettings('pts', 'route_builder')



def fixHeaders(path):
    with open(path) as f:
        t=f.read()
    r={'qgsfieldcombobox.h':'qgis.gui','qgsmaplayercombobox.h':'qgis.gui'}
    for i in r:
        t=t.replace(i,r[i])
    with open(path, "w") as f:
        f.write(t)
        
        
uiPath=os.path.join(os.path.dirname(__file__), 'route_builder_dockwidget_base.ui')
fixHeaders(uiPath)
FORM_CLASS, _ = uic.loadUiType(uiPath)
	
	
class route_builderDockWidget(QtGui.QDockWidget, FORM_CLASS):

    closingPlugin = pyqtSignal()
    def __init__(self, parent=None):
        """Constructor."""
        super(route_builderDockWidget, self).__init__(parent)
        self.setupUi(self)
        self.routes=[]#list avoids need for unique names
        
        self.field_boxes=[self.label_field_box,self.length_field_box,self.rbt_field_box,self.snode_field_box,self.enode_field_box,self.description_field_box]
        
        self.label_field_box.setFilters(QgsFieldProxyModel.String)
        self.length_field_box.setFilters(QgsFieldProxyModel.Double|QgsFieldProxyModel.Int)
        
        self.network_layer_box.layerChanged.connect(self.layer_changed)
        if self.network_layer_box.currentLayer():
            self.layer_changed(self.network_layer_box.currentLayer())
        
        self.new_button.clicked.connect(self.new_route)
        self.delete_button.clicked.connect(self.delete_route)
        self.routes_box.currentIndexChanged.connect(self.route_changed)
        self.name_edit.textEdited.connect(self.change_name)
        self.desc_edit.textChanged.connect(self.change_desc)
        self.date_edit.dateChanged.connect(self.change_date)
        
        self.sections_view.setContextMenuPolicy(Qt.CustomContextMenu);
        self.sections_view.customContextMenuRequested.connect(self.menu)
        
        self.menu=QtGui.QMenuBar(self)
        
        export_menu= self.menu.addMenu('Export...')
        self.to_layer_act=export_menu.addAction('To QGIS layer')
        self.to_layer_act.triggered.connect(self.to_layer)
        
        
       
        
        self.load_fields()
        
        for f in self.field_boxes:
            f.fieldChanged.connect(self.save_fields)
        
        
        
    def save_fields(self):        
        settings.setValue('fields',[f.currentText() for f in self.field_boxes])
        settings.setValue('layer',self.network_layer_box.currentLayer().name())
        
        
        
        #for each layer with same name try setting field_boxes to this layer and fields. return if works.
    def load_fields(self):    
        for layer in find_layers(self.network_layer_box,settings.value('layer')):
            try:
                fields=settings.value('fields')
                self.network_layer_box.setLayer(layer)#triggers layer_changed(), setting field_boxes to layer
                
                
                for i,f in enumerate(self.field_boxes):
                  #  f.setLayer(layer)
                    f.setField(fields[i])
                return
            except:
                pass
            
        
        
    def new_route(self):
        self.routes.append(route.route('route_no',survey_date=QDate.currentDate()))
        self.routes_box.addItems(['route_no'])
        
        
    def delete_route(self):
        i=self.routes_box.currentIndex()
        if i!=-1:
            q='delete route %s?'%(self.routes_box.currentText())
            
            reply = QtGui.QMessageBox.question(self, 'delete route', 
                     q, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)        
            
            if reply == QtGui.QMessageBox.Yes:
                del self.routes[i]
                self.routes_box.removeItem(i)
                
                
    def route_changed(self,i):
        if i!=-1:
            self.name_edit.setText(self.routes[i].name)
            self.desc_edit.setPlainText(self.routes[i].desc)
            self.date_edit.setDate(self.routes[i].survey_date)
            self.sections_view.setModel(self.routes[i].model)
        
        
    def current_route(self):
        i=self.routes_box.currentIndex()
        if i!=-1:
            return self.routes[i]
        
        
    def change_name(self,name):
        i=self.routes_box.currentIndex()
        if i!=-1:
            self.routes[i].name=name
            self.routes_box.setItemText(i,name)
        
        
    def change_desc(self):
        if self.current_route():
            self.current_route().desc=self.desc_edit.toPlainText()        
        
        
    def change_date(self,date):
        if self.current_route():
            self.current_route().survey_date=date
            
    
    def menu(self,pt):
        menu = QMenu()
        from_layer = menu.addAction("add section from layer")
        from_layer.setShortcut("Ctrl+1")
        from_layer.setToolTip('Add selected section of layer. Shortcut CTRL 1')
        from_layer_rev = menu.addAction("add section from layer (reverse direction)")
        from_layer.setToolTip('Add selected section of layer(reverse direction). Shortcut CTRL 2')
        from_layer_rev.setShortcut("Ctrl+2")
        del_sects = menu.addAction("delete selected sections")

        action = menu.exec_(self.mapToGlobal(pt))
        if action==from_layer:
            self.add_from_layer()
        if action==from_layer_rev:
            self.add_from_layer(True)
            

    def add_from_layer(self,rev=False):
        layer=self.network_layer_box.currentLayer()
        sf=layer.selectedFeatures()
        
        
        if self.check_fields():
        
            if len(sf)==0:
                iface.messageBar().pushMessage('route builder: no features selected on layer '+layer.name())
                return
            if len(sf)>1:
                iface.messageBar().pushMessage('route builder: >1 feature selected on layer '+layer.name())
                return
            
            f=sf[0]
        #    def add_section(self,label,snode,rev,length,rbt,ch,desc,wkt):
            
            if self.current_route():
                geom=f.geometry()
                geom.transform(self.transform)#transform to osgb
                
                
                if rev:
                    #add_section(self,label,snode,rev,length,rbt,ch,desc,wkt)
                    self.current_route().add_section(self.get_val(self.label_field_box,f),self.get_val(self.enode_field_box,f),rev,
                                   self.get_val(self.length_field_box,f),self.get_val(self.rbt_field_box,f,False),0,self.get_val(self.description_field_box,f),
                                  geom.exportToWkt())# g.geometry().asWkt()))) for qgis 3
                    
                else:
                    self.current_route().add_section(self.get_val(self.label_field_box,f),self.get_val(self.snode_field_box,f),rev,
                                   self.get_val(self.length_field_box,f),self.get_val(self.rbt_field_box,f,False),0,self.get_val(self.description_field_box,f),
                                  geom.exportToWkt())# g.geometry().asWkt()))) for qgis 3
            else:
                pt('route builder: no route selected')
                

    def to_layer(self):
        layer=route.initialise_layer()
        
        layer.startEditing()
        
        for r in self.routes:
            #layer.dataProvider().addFeatures(r.to_features(layer))
            
            layer.addFeatures(r.to_features(layer))
        
        layer.commitChanges()
            #pt(r.name)
                    
    #check  layer not None, required fields label,length filled in 
    def check_fields(self):
        if self.network_layer_box.currentLayer() is None:
            pt('route builder: no layer selected. Check settings tab.')
            return False
        
        
        if self.label_field_box.currentIndex()==-1:
            pt('route builder: label field not set. Check settings tab.')
            return False
        
        if self.length_field_box.currentIndex()==-1:
            pt('route builder: length field not set. Check settings tab.')        
            return False
        
        return True
        
    
    def get_val(self,field_box,feat,default=''):
        if field_box.currentText():
            return feat[field_box.currentText()]
        else:
            return default
    
    
    def layer_changed(self,layer):
        for f in self.field_boxes:
            f.setLayer(layer)
        
        
        #self.label_field_box.setLayer(layer)
        #self.length_field_box.setLayer(layer)
        #self.rbt_field_box.setLayer(layer)
        #self.snode_field_box.setLayer(layer)
        #self.enode_field_box.setLayer(layer)
        #self.description_field_box.setLayer(layer)

        source_crs = layer.crs()
        dest_crs = QgsCoordinateReferenceSystem()
        dest_crs.createFromString('ESPG:27700')
        self.transform=QgsCoordinateTransform(source_crs, dest_crs)
       # myGeometryInstance.transform(tr)    

            
def pt(s):
    iface.messageBar().pushMessage(str(s))
    

def find_layers(box,name):  
    return [box.layer(i) for i in range(0,box.count()) if box.layer(i).name()==name]
        

def find_fields(box,name):  
    return [box.layer(i) for i in range(0,box.rowCount()) if box.layer(i).name()==name]
        
