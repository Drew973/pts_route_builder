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
        
    
    #def add_section(self,label,snode,rev,length,rbt,ch,desc,wkt,row=0):
#        #self.model.insertRow(row,[make_cell(label),make_cell(rev,True),make_cell(desc,True),make_cell(ch),make_cell(snode),make_cell(length),make_cell(rbt),make_cell(wkt)])

    def add_section(self,label,rev,desc,ch,snode,length,rbt,wkt,row=0):
        self.model.insertRow(row,[make_cell(label),make_cell(rev,True),make_cell(desc,True),make_cell(ch),make_cell(snode),make_cell(length),make_cell(rbt),make_cell(wkt)])

    
    #converts to qgis features
    def to_features(self,layer):        
        return [self.to_feat(i,layer) for i in range(0,self.model.rowCount())]
    

    def remove_rows(self,rows):
        # removing changes following row numbers.Start with highest row number.
        for r in reversed(sorted(rows)):
            self.model.takeRow(r)
    
    
    #key like [route_att:feature_att]
        
    def add_feat(self,f,transform,row,rev,key):
        geom=f.geometry()
        geom.transform(transform)
        
        snode=f[key['snode']]
        
        if rev:
            geom=reversed_geom(geom)
            snode=f[key['enode']]
        
        #chainage will be recalculated so irrelevant
        self.add_section(f[key['section_label']],rev,f[key['section_description']],0,
                        snode,f[key['section_length']],f[key['roundabout']], geom.exportToWkt(),row)
        
        
        
        # g.geometry().asWkt()))) for qgis 3
        
        
        
        
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
       
        if self.get_val(row,cols['reversed']):
            geom=reversed_geom(QgsGeometry.fromWkt(self.get_val(row,cols['wkt'])))
        else:
            geom=QgsGeometry.fromWkt(self.get_val(row,cols['wkt']))
            
        feat.setGeometry(geom)
        return feat
       
        
    def get_val(self,row,col):
        return self.model.item(row,col).data(Qt.EditRole)
    
    
    def __eq__(self,other):
        return self.name==other.name and self.desc==other.desc and self.run_no==other.run_no#and self.survey_date=other.survey_date
    
    
    #def __add__(self,other):
     #   if self==other:
      #      r=route(self.name,self.desc,self.survey_date,self.run_no)
       # else:
        #    raise ValueError('conflicting route data')
    
    
    def consume_other(self,other):
        if self==other:
            for i in other.model.rowCount():
                self.model.appendRow(other.model.takeRow(i))
    
        else:
            raise ValueError('conflicting route data')
        
        
def make_cell(val,editable=False):
    cell=QStandardItem()
    cell.setEditable(editable)
    cell.setData(val,Qt.EditRole)
    cell.setDropEnabled(False)
    return cell


from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsMapLayerRegistry,QgsVectorLayer,QgsField


FIELDS={'route':QVariant.String,'route_description':QVariant.String,'survey_date':QVariant.String,'run_no':QVariant.String,
        'section_label':QVariant.String,'reversed':QVariant.String,'section_description':QVariant.String,'chainage':QVariant.Double,
        'snode':QVariant.String,'section_length':QVariant.Double,'roundabout': QVariant.String}


def initialise_layer(name):
    vl=QgsVectorLayer("Linestring", name, "memory")
    
    fields=[QgsField(f,FIELDS[f]) for f in FIELDS]
    
    vl.dataProvider().addAttributes(fields)
    vl.updateFields()
    QgsMapLayerRegistry.instance().addMapLayer(vl)    
    return vl


def pt(s):
    iface.messageBar().pushMessage(str(s))


def reversed_geom(geom):
    nodes=geom.asPolyline()
    nodes.reverse()
    return QgsGeometry.fromPolyline(nodes)#reverse direction



def feat_to_route(f):
    r=route(f['route'],f['route_description'],f['survey_date'],f['run_no'])