class section:
    
    
    def __init__(self,label,rev,desc,ch,snode,length,rbt,wkt):
        self.label=label
        self.rev=rev
        self.desc=desc
        self.ch=ch
        self.snode=snode
        self.length=length
        self.rbt=rbt
        self.wkt=wkt
        
        
        
    def __getitem__(self,key):
        if key==0:
            return self.label
        if key==1:
            return self.rev
        if key==2:
            return self.desc
        if key==3:
            return self.ch
        if key==4:
            return self.snode
        if key==5:
            return self.length
        if key==6:
            return self.rbt
        if key==7:
            return self.wkt