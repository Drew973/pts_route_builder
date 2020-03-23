import os
from  qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog
from qgis.PyQt import  QtGui

from qgis.gui import QgsFieldProxyModel,QgsMapLayerComboBox

import route

#uiPath=os.path.join(os.path.dirname(__file__), 'read_csv_dialog.ui')
#FORM_CLASS, _ = uic.loadUiType(uiPath)

from qgis.utils import iface

#from qgis.PyQt.QtCore import Qt


class load_layer_dialog(QDialog):
    
    def __init__(self,parent=None,routes=[]):
        super(QDialog,self).__init__(parent)
        self.setModal(True)#modal blocks other stuff
        self.layer_box=QgsMapLayerComboBox()
        self.ok_button=QtGui.QPushButton('Ok')
        self.cancel_button=QtGui.QPushButton('Cancel')
        
        layout=QtGui.QHBoxLayout(self)
        layout.addWidget(self.layer_box)
        layout.addWidget(self.ok_button)
        layout.addWidget(self.cancel_button)
        
        self.routes=routes
        self.ok_button.clicked.connect(self.load)
        self.cancel_button.clicked.connect(self.reject)
        
        
    def load(self):
        load_layer(self.layer_box.currentLayer(),self.routes)
        self.accept()
        
        
def pt(s,duration):
    iface.messageBar().pushMessage(str(s),duration=duration)
        
        
    
#check layer contains correct field names and types
def check_fields(layer):    
    fields={f.name():f.type() for f in layer.fields()}
   
    for f in route.FIELDS:
        if not f in fields:
            return False
        else:
            if not fields[f]==route.FIELDS[f]:
                return False
    
    return True
                

type_key={10:'QString',6:'Double'}    

#check layer contains correct field names and types
def missing_fields(layer):    
    missing={}
    
    #fields={f.name():f.type() for f in layer.fields()}
    fields={f.name():f.typeName() for f in layer.fields()}
    
    
    for f in route.FIELDS:
        if not f in fields:
            missing.update({f:'missing'})
        else:
            if not fields[f]==route.FIELDS[f]:
                #tp=fields[f]
                missing.update({f:'wrong type. Is %s. Need %s'%(fields[f], route.FIELDS[f])})
    
    return missing   
    


def load_layer(layer,routes):
    missing=missing_fields(layer)
    if missing:
        pt('route builder: Missing or incorrect fields:'+str(missing)[1:-1],10)
