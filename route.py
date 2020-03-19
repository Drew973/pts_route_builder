from PyQt4.QtGui import QStandardItem,QStandardItemModel#QMenu
from PyQt4.QtCore import Qt,QAbstractTableModel

from qgis.core import QgsFeature,QgsFeatureRequest,QgsExpression,QgsGeometry

import route_model

from qgis.utils import iface


cols={'section_label':0,'reversed':1,'section_description':2,'chainage':3,'snode':4,'section_length':5,'roundabout':6,'wkt':7}


class route:
    def __init__(self,name='',desc='',survey_date=None,run_no=''):
        self.name=name
        self.desc=desc
        self.survey_date=survey_date
        self.run_no=run_no
        
        self.model=QStandardItemModel()
        #self.model=route_model.route_model()
        
        self.model.setColumnCount(len(cols))
       
        [self.model.setHeaderData(cols[c], Qt.Horizontal,c) for c in cols]
        
      
    
    
    def add_section(self,label,snode,rev,length,rbt,ch,desc,wkt):
        self.model.appendRow([make_cell(label),make_cell(rev,True),make_cell(desc,True),make_cell(ch),make_cell(snode),make_cell(length),make_cell(rbt),make_cell(wkt)])
    
    
    #converts to qgis features
    def to_features(self,layer):        
        return [self.to_feat(i,layer) for i in range(0,self.model.rowCount())]
        
        
    #make qgis feature from row of model
    def to_feat(self,row,layer):
        
        feat = QgsFeature(layer.fields())
        
        for c in cols:
            if c!='wkt':
                feat.setAttribute(c,self.get_val(row,cols[c]))
            
        feat.setAttribute('route',self.name)
        feat.setAttribute('route_description',self.desc)
        feat.setAttribute('survey_date',self.desc)
        feat.setAttribute('run_no',self.run_no)
       
        geom=QgsGeometry.fromWkt(self.get_val(row,cols['wkt']))
        feat.setGeometry(geom)
        return feat
       
        
    def get_val(self,row,col):
        return self.model.item(row,col).data(Qt.EditRole)
    
    
def make_cell(val,editable=False):
    cell=QStandardItem()
    cell.setEditable(editable)
    cell.setData(val,Qt.EditRole)
    cell.setDropEnabled(False)
    return cell


from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsMapLayerRegistry,QgsVectorLayer,QgsField



def initialise_layer(name='route builder output'):
    vl=QgsVectorLayer("Linestring", name, "memory")
    
    
    fields=[QgsField('route', QVariant.String),
            QgsField('route_description', QVariant.String),
            QgsField('survey_date', QVariant.String),#qgis can't handle dates.
            QgsField('run_no', QVariant.String),
            QgsField('section_label', QVariant.String),
            QgsField('reversed', QVariant.String),
            QgsField('section_description', QVariant.String),
            QgsField('chainage', QVariant.Double),
            QgsField('snode', QVariant.String),
            QgsField('section_length', QVariant.Double),
            QgsField('roundabout', QVariant.String)
    ]
    
    vl.dataProvider().addAttributes(fields)
    vl.updateFields()
    QgsMapLayerRegistry.instance().addMapLayer(vl)    
    return vl

def pt(s):
    iface.messageBar().pushMessage(str(s))


