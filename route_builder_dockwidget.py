# -*- coding: utf-8 -*-
import os
from PyQt4 import QtGui, uic
from qgis.PyQt.QtCore import pyqtSignal,QDate,Qt

import route
from qgis.utils import iface
from PyQt4.QtGui import QMenu,QWidgetAction

from qgis.core import QgsCoordinateReferenceSystem,QgsCoordinateTransform,QgsProject,QgsGeometry
from qgis.gui import QgsFieldProxyModel,QgsMapLayerComboBox

from qgis.PyQt.QtCore import QSettings
settings=QSettings('pts', 'route_builder')

import load_layer

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
        self.run_no_edit.textEdited.connect(self.change_run_no)
        

        
        self.load_fields()
        
        for f in self.field_boxes:
            f.fieldChanged.connect(self.save_fields)
        
        self.init_sections_menu()
        self.init_top_menu()
        
        
    def init_top_menu(self):
        self.top_menu=QtGui.QMenuBar(self)
        export_menu= self.top_menu.addMenu('Export')
        self.to_layer_act=export_menu.addAction('To QGIS layer')
        self.to_layer_act.triggered.connect(self.to_layer)
        
        load_menu= self.top_menu.addMenu('Load')
        
        load_layer_act=load_menu.addAction('Load QGIS layer...')
        load_layer_act.triggered.connect(self.load_layer)
        
        
        
        #load_layer_act=QWidgetAction(self)
        #load_layer_act.setDefaultWidget(QgsMapLayerComboBox())
        #load_menu.addAction(load_layer_act)
        
        
    def load_layer(self):
        load_layer.load_layer_dialog(self,self.routes).exec_()
        #read_csv_dialog(self.hmd).exec_()
        pass
        
    
        
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
            self.run_no_edit.setText(self.routes[i].run_no)
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
     
        
    def change_run_no(self,run_no):
        if self.current_route():
            self.current_route().run_no=run_no      
        
        
    def init_sections_menu(self):
        self.sections_menu = QMenu()
        from_layer = self.sections_menu.addAction("add section from layer")
        from_layer.setShortcut("Ctrl+1")
        from_layer.setToolTip('Add selected section of layer.')        
        from_layer.triggered.connect(self.add_from_layer_f)

        from_layer_rev = self.sections_menu.addAction("add section from layer (reverse direction)")
        from_layer.setToolTip('Add selected section of layer(reverse direction).')
        from_layer_rev.setShortcut("Ctrl+2")
        from_layer_rev.triggered.connect(self.add_from_layer_r)#############################################
        
        del_selected = self.sections_menu.addAction("remove selected rows")
        del_selected.setShortcut("Ctrl+3")
        del_selected.triggered.connect(self.remove_selected)#############################################
        
        
        self.sections_view.setContextMenuPolicy(Qt.CustomContextMenu);
        self.sections_view.customContextMenuRequested.connect(self.show_sections_menu)
        
        
    def show_sections_menu(self,pt):
        self.sections_menu.exec_(self.mapToGlobal(pt))
       
        
    def remove_selected(self):
        if self.current_route():
          self.current_route().remove_rows(self.selected_sections())
        
        
    def selected_sections(self):
        rows=[r.row() for r in self.sections_view.selectionModel().selectedRows()]
        return list(set(sorted(rows)))#sorted list of unique rows
        
    
    def add_from_layer_f(self):
        self.add_from_layer(False)
        
        
    def add_from_layer_r(self):
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
            
            if self.current_route():
                geom=f.geometry()
                geom.transform(self.transform)#transform to osgb
                
                if self.selected_sections():
                    row=self.selected_sections()[-1]+1#row after last selected
                else:
                    row=0
                    
                if rev:
                    #add_section(self,label,snode,rev,length,rbt,ch,desc,wkt)
                    self.current_route().add_section(self.get_val(self.label_field_box,f),self.get_val(self.enode_field_box,f),rev,
                                   self.get_val(self.length_field_box,f),self.get_val(self.rbt_field_box,f,False),0,self.get_val(self.description_field_box,f),
                                  geom.exportToWkt(),row)# g.geometry().asWkt()))) for qgis 3
                    
                else:
                    self.current_route().add_section(self.get_val(self.label_field_box,f),self.get_val(self.snode_field_box,f),rev,
                                   self.get_val(self.length_field_box,f),self.get_val(self.rbt_field_box,f,False),0,self.get_val(self.description_field_box,f),
                                  geom.exportToWkt(),row)# g.geometry().asWkt()))) for qgis 3
            else:
                pt('route builder: no route selected')
                

    def to_layer(self):
        name='route builder output'
        layer=route.initialise_layer(name)
        
        layer.startEditing()
        
        for r in self.routes:
            #layer.dataProvider().addFeatures(r.to_features(layer))
            
            layer.addFeatures(r.to_features(layer))
        
        layer.commitChanges()
        pt('route builder: made memory layer %s. THIS WILL BE LOST ON QUITING QGIS.'%(name))

                    
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
        
    
    def fields_key(self):
        cols={'section_label':0,'reversed':1,'section_description':2,'chainage':3,'snode':4,'section_length':5,'roundabout':6}
self.field_boxes=[self.label_field_box,self.length_field_box,self.rbt_field_box,self.snode_field_box,self.enode_field_box,self.description_field_box]
    
        return {'section_label':self.label_field_box.currentText(),'section_description':self.description_field_box.currentText(),'snode':snode_field_box.currentText(),
                'section_length':self.length_field_box.CurrentText(),'roundabout':self.rbt_field_box.currentText()
                }


    
    def get_val(self,field_box,feat,default=''):
        if field_box.currentText():
            return feat[field_box.currentText()]
        else:
            return default
    
    
    def layer_changed(self,layer):
        for f in self.field_boxes:
            f.setLayer(layer)
        
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
        
