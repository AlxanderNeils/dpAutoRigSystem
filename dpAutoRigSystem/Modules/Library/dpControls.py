# importing libraries:
from maya import cmds
from maya import mel
from . import dpUtils
from ...Validator.CheckOut import dpResetPose
from functools import partial
import os
import getpass
import datetime

DPCONTROL = "dpControl"
SNAPSHOT_SUFFIX = "_Snapshot_Crv"

dic_colors = {
    "yellow": 17,
    "red": 13,
    "blue": 6,
    "cyan": 18,
    "green": 7,
    "darkRed": 4,
    "darkBlue": 15,
    "white": 16,
    "black": 1,
    "gray": 3,
    "bonina": [0.38, 0, 0.15],
    "none": 0,
}

DP_CONTROLS_VERSION = 2.3


class ControlClass(object):

    def __init__(self, dpUIinst, moduleGrp=None, *args):
        """ Initialize the module class defining variables to use creating preset controls.
        """
        # defining variables:
        self.dpUIinst = dpUIinst
        self.attrValueDic = {}
        self.moduleGrp = moduleGrp
        self.resetPose = dpResetPose.ResetPose(self.dpUIinst, ui=False, verbose=False)
        self.ignoreDefaultValuesAttrList = ["translateX", "translateY", "translateZ", "rotateX", "rotateY", "rotateZ", "scaleX", "scaleY", "scaleZ", "visibility", "rotateOrder", "scaleCompensate"]
        self.defaultValueWindowName = "dpDefaultValueOptionWindow"
        self.doingName = self.dpUIinst.lang['m094_doing']


    # CONTROLS functions:
    def colorShape(self, objList, color, rgb=False, outliner=False, *args):
        """ Create a color override for all shapes from the objList.
        """
        iColorIdx = color
        if rgb:
            if color in list(dic_colors):
                color = dic_colors[color]
        elif color in list(dic_colors):
            iColorIdx = dic_colors[color]

        # find shapes and apply the color override:
        shapeTypeList = ['nurbsCurve', 'nurbsSurface', 'mesh', 'subdiv']
        if objList:
            for objName in objList:
                if outliner:
                    self.setColorOverride(objName, color, iColorIdx, rgb, outliner)
                else:
                    objType = cmds.objectType(objName)
                    # verify if the object is the shape type:
                    if objType in shapeTypeList:
                        self.setColorOverride(objName, color, iColorIdx, rgb)
                    # verify if the object is a transform type:
                    elif objType == "transform":
                        # find all shapes children of the transform object:
                        shapeList = cmds.listRelatives(objName, shapes=True, children=True, fullPath=True)
                        if shapeList:
                            for shape in shapeList:
                                self.setColorOverride(shape, color, iColorIdx, rgb)


    def setColorOverride(self, item, color, iColorIdx, rgb, outliner=False, *args):
        """ Set the color for the given node and color data.
        """
        if outliner:
            cmds.setAttr(item+".useOutlinerColor", 1)
            cmds.setAttr(item+".outlinerColor.outlinerColorR", color[0])
            cmds.setAttr(item+".outlinerColor.outlinerColorG", color[1])
            cmds.setAttr(item+".outlinerColor.outlinerColorB", color[2])
            mel.eval('source AEdagNodeCommon;')
            mel.eval("AEdagNodeCommonRefreshOutliners();")
        else:
            # set override as enable:
            cmds.setAttr(item+".overrideEnabled", 1)
            # set color override:
            if rgb:
                cmds.setAttr(item+".overrideRGBColors", 1)
                cmds.setAttr(item+".overrideColorR", color[0])
                cmds.setAttr(item+".overrideColorG", color[1])
                cmds.setAttr(item+".overrideColorB", color[2])
            else:
                cmds.setAttr(item+".overrideRGBColors", 0)
                cmds.setAttr(item+".overrideColor", iColorIdx)


    def removeColor(self, itemList, *args):
        """ Just remove color of given list or selected nodes.
        """
        if not itemList:
            itemList = cmds.ls(selection=True)
        if itemList:
            for item in itemList:
                cmds.setAttr(item+".overrideEnabled", 0)
                cmds.setAttr(item+".overrideRGBColors", 0)
                cmds.setAttr(item+".useOutlinerColor", 0)


    def renameShape(self, transformList, *args):
        """Find shapes, rename them to Shapes and return the results.
        """
        resultList = []
        for transform in transformList:
            # list all children shapes:
            childShapeList = cmds.listRelatives(transform, shapes=True, children=True, fullPath=True)
            if childShapeList:
                for i, child in enumerate(childShapeList):
                    shapeName = transform+str(i)+"Shape"
                    shape = cmds.rename(child, shapeName)
                    resultList.append(shape)
                cmds.select(clear=True)
            else:
                print("There are not children shape to rename inside of:", transform)
        return resultList


    def directConnect(self, fromObj, toObj, attrList=['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'], f=True, *args):
        """Connect attributes from list directely between two objects given.
        """
        if cmds.objExists(fromObj) and cmds.objExists(toObj):
            for attr in attrList:
                try:
                    # connect attributes:
                    cmds.connectAttr(fromObj+"."+attr, toObj+"."+attr, force=f)
                except:
                    print("Error: Cannot connect", toObj, ".", attr, "directely.")
        
        
    def setLockHide(self, objList, attrList, l=True, k=False, cb=False, *args):
        """Set lock or hide to attributes for object in lists.
        """
        if objList and attrList:
            for obj in objList:
                for attr in attrList:
                    try:
                        # set lock and hide of given attributes:
                        cmds.setAttr(obj+"."+attr, lock=l, keyable=k, channelBox=cb)
                    except:
                        print("Error: Cannot set", obj, ".", attr, "as lock=", l, "and keyable=", k, "and channelBox=", cb)
                        
                        
    def setNonKeyable(self, objList, attrList, *args):
        """Set nonKeyable to attributes for objects in lists.
        """
        if objList and attrList:
            for obj in objList:
                for attr in attrList:
                    if cmds.objExists(obj+"."+attr):
                        try:
                            # set lock and hide of given attributes:
                            cmds.setAttr(obj+"."+attr, keyable=False, channelBox=True)
                        except:
                            print("Error: Cannot set", obj, ".", attr, "as nonKeayble, sorry.")


    def setNotRenderable(self, objList, *args):
        """Receive a list of objects, find its shapes if necessary and set all as not renderable.
        """
        # declare a list of attributes for render:
        renderAttrList = ["castsShadows", "receiveShadows", "motionBlur", "primaryVisibility", "smoothShading", "visibleInReflections", "visibleInRefractions", "doubleSided", "miTransparencyCast", "miTransparencyReceive", "miReflectionReceive", "miRefractionReceive", "miFinalGatherCast", "miFinalGatherReceive"]
        shapeTypeList = ['nurbsCurve', 'nurbsSurface', 'mesh', 'subdiv']
        # find all children shapes:
        if objList:
            for obj in objList:
                objType = cmds.objectType(obj)
                # verify if the object is the shape type:
                if objType in shapeTypeList:
                    # set attributes as not renderable:
                    for attr in renderAttrList:
                        try:
                            cmds.setAttr(obj+"."+attr, 0)
                        except:
                            #print("Error: Cannot set not renderable ", attr, "as zero for", obj)
                            pass
                # verify if the object is a transform type:
                elif objType == "transform":
                    # find all shapes children of the transform object:
                    shapeList = cmds.listRelatives(obj, shapes=True, children=True)
                    if shapeList:
                        for shape in shapeList:
                            # set attributes as not renderable:
                            for attr in renderAttrList:
                                try:
                                    cmds.setAttr(shape+"."+attr, 0)
                                except:
                                    #print("Error: Cannot set not renderable ", attr, "as zero for", shape)
                                    pass

    
    def createSimpleRibbon(self, name='ribbon', totalJoints=6, jointLabelNumber=0, jointLabelName="SimpleRibbon", *args):
        """ Creates a Ribbon system.
            Receives the total number of joints to create.
            Returns the ribbon nurbs plane, the joints groups and joints created.
        """
        # create a ribbonNurbsPlane:
        ribbonNurbsPlane = cmds.nurbsPlane(name=name+"RibbonNurbsPlane", constructionHistory=False, object=True, polygon=0, axis=(0, 1, 0), width=1, lengthRatio=8, patchesV=totalJoints)[0]
        # get the ribbonNurbsPlane shape:
        ribbonNurbsPlaneShape = cmds.listRelatives(ribbonNurbsPlane, shapes=True, children=True)[0]
        # make this ribbonNurbsPlane as template, invisible and not renderable:
        cmds.setAttr(ribbonNurbsPlane+".template", 1)
        cmds.setAttr(ribbonNurbsPlane+".visibility", 0)
        self.setNotRenderable([ribbonNurbsPlaneShape])
        # make this ribbonNurbsPlane as not skinable from dpAR_UI:
        cmds.addAttr(ribbonNurbsPlane, longName="dpDoNotSkinIt", attributeType="bool", keyable=True, defaultValue=True)
        # create groups to be used as a root of the ribbon system:
        ribbonGrp = cmds.group(ribbonNurbsPlane, n=name+"_Rbn_RibbonJoint_Grp")
        # create joints:
        jointList, jointGrpList = [], []
        for j in range(totalJoints+1):
            # create pointOnSurfaceInfo:
            infoNode = cmds.createNode('pointOnSurfaceInfo', name=name+"_POSI"+str(j+1))
            # setting parameters worldSpace, U and V:
            cmds.connectAttr(ribbonNurbsPlaneShape + ".worldSpace[0]", infoNode + ".inputSurface")
            cmds.setAttr(infoNode + ".parameterV", ((1/float(totalJoints))*j) )
            cmds.setAttr(infoNode + ".parameterU", 0.5)
            # create and parent groups to calculate:
            posGrp = cmds.group(n=name+"Pos"+str(j+1)+"_Grp", empty=True)
            upGrp  = cmds.group(n=name+"Up"+str(j+1)+"_Grp", empty=True)
            aimGrp = cmds.group(n=name+"Aim"+str(j+1)+"_Grp", empty=True)
            cmds.parent(upGrp, aimGrp, posGrp, relative=True)
            # connect groups translations:
            cmds.connectAttr(infoNode + ".position", posGrp + ".translate", force=True)
            cmds.connectAttr(infoNode + ".tangentU", upGrp + ".translate", force=True)
            cmds.connectAttr(infoNode + ".tangentV", aimGrp + ".translate", force=True)
            # create joint:
            cmds.select(clear=True)
            joint = cmds.joint(name=name+"_%02d_Jnt"%(j+1))
            jointList.append(joint)
            cmds.addAttr(joint, longName='dpAR_joint', attributeType='float', keyable=False)
            # parent the joint to the groups:
            cmds.parent(joint, posGrp, relative=True)
            jointGrp = cmds.group(joint, name=name+"Joint"+str(j+1)+"_Grp")
            jointGrpList.append(jointGrp)
            # create aimConstraint from aimGrp to jointGrp:
            cmds.aimConstraint(aimGrp, jointGrp, offset=(0, 0, 0), weight=1, aimVector=(0, 1, 0), upVector=(0, 0, 1), worldUpType="object", worldUpObject=upGrp, n=name+"Ribbon"+str(j)+"_AiC" )
            # parent this ribbonPos to the ribbonGrp:
            cmds.parent(posGrp, ribbonGrp, absolute=True)
            # joint labelling:
            dpUtils.setJointLabel(joint, jointLabelNumber, 18, jointLabelName+"_%02d"%(j+1))
        return [ribbonNurbsPlane, ribbonNurbsPlaneShape, jointGrpList, jointList]
    
    
    def getControlNodeById(self, ctrlType, *args):
        """ Find and return node list with ctrlType in its attribute.
        """
        ctrlList = []
        allTransformList = cmds.ls(selection=False, type="transform")
        for item in allTransformList:
            if cmds.objExists(item+".controlID"):
                if cmds.getAttr(item+".controlID") == ctrlType:
                    ctrlList.append(item)
        return ctrlList
    
    
    def getControlModuleById(self, ctrlType, *args):
        """ Check the control type reading the loaded dictionary from preset json file.
            Return the respective control module name by id.
        """
        ctrlModule = self.dpUIinst.ctrlPreset[ctrlType]['type']
        return ctrlModule
        
        
    def getControlDegreeById(self, ctrlType, *args):
        """ Check the control type reading the loaded dictionary from preset json file.
            Return the respective control module name by id.
        """
        ctrlModule = self.dpUIinst.ctrlPreset[ctrlType]['degree']
        return ctrlModule


    def getControlInstance(self, instanceName, *args):
        """ Find the loaded control instance by name.
            Return the instance found.
        """
        if self.dpUIinst.controlInstanceList:
            for instance in self.dpUIinst.controlInstanceList:
                if instance.guideModuleName == instanceName:
                    return instance


    def cvControl(self, ctrlType, ctrlName, r=1, d=1, dir='+Y', rot=(0, 0, 0), corrective=False, *args):
        """ Create and return a curve to be used as a control.
            Check if the ctrlType starts with 'id_###_Abc' and get the control type from json file.
            Otherwise, check if ctrlType is a valid control curve object in order to create it.
        """
        # get control module:
        if ctrlType.startswith("id_"):
            ctrlModule = self.getControlModuleById(ctrlType)
            # get degree:
            if d == 0:
                d = self.getControlDegreeById(ctrlType)
        else:
            ctrlModule = ctrlType
            if d == 0:
                d = 1
        # get control instance:
        controlInstance = self.getControlInstance(ctrlModule)
        if controlInstance:
            # create curve
            curve = controlInstance.cvMain(False, ctrlType, ctrlName, r, d, dir, rot, 1)
            if corrective:
                self.addCorrectiveAttrs(curve)
            return curve


    def cvLocator(self, ctrlName, r=1, d=1, guide=False, *args):
        """ Create and return a cvLocator curve to be usually used in the guideSystem.
        """
        curveInstance = self.getControlInstance("Locator")
        curve = curveInstance.cvMain(False, "Locator", ctrlName, r, d, '+Y', (0, 0, 0), 1, guide)
        if guide:
            self.addGuideAttrs(curve)
        return curve


    #@dpUtils.profiler
    def cvJointLoc(self, ctrlName, r=0.3, d=1, rot=(0, 0, 0), guide=True, *args):
        """ Create and return a cvJointLocator curve to be usually used in the guideSystem.
        """
        # create locator curve:
        cvLoc = self.cvLocator(ctrlName+"_CvLoc", r, d)
        # create arrow curves:
        cvArrow1 = cmds.curve(n=ctrlName+"_CvArrow1", d=3, p=[(-0.1*r, 0.9*r, 0.2*r), (-0.1*r, 0.9*r, 0.23*r), (-0.1*r, 0.9*r, 0.27*r), (-0.1*r, 0.9*r, 0.29*r), (-0.1*r, 0.9*r, 0.3*r), (-0.372*r, 0.9*r, 0.24*r), (-0.45*r, 0.9*r, -0.13*r), (-0.18*r, 0.9*r, -0.345*r), (-0.17*r, 0.9*r, -0.31*r), (-0.26*r, 0.9*r, -0.41*r), (-0.21*r, 0.9*r, -0.41*r), (-0.05*r, 0.9*r, -0.4*r), (0, 0.9*r, -0.4*r), (-0.029*r, 0.9*r, -0.33*r), (-0.048*r, 0.9*r, -0.22*r), (-0.055*r, 0.9*r, -0.16*r), (-0.15*r, 0.9*r, -0.272*r), (-0.12*r, 0.9*r, -0.27*r), (-0.35*r, 0.9*r, -0.1*r), (-0.29*r, 0.9*r, 0.15*r), (-0.16*r, 0.9*r, 0.21*r), (-0.1*r, 0.9*r, 0.2*r)] )
        cvArrow2 = cmds.curve(n=ctrlName+"_CvArrow2", d=3, p=[(0.1*r, 0.9*r, -0.2*r), (0.1*r, 0.9*r, -0.23*r), (0.1*r, 0.9*r, -0.27*r), (0.1*r, 0.9*r, -0.29*r), (0.1*r, 0.9*r, -0.3*r), (0.372*r, 0.9*r, -0.24*r), (0.45*r, 0.9*r, 0.13*r), (0.18*r, 0.9*r, 0.345*r), (0.17*r, 0.9*r, 0.31*r), (0.26*r, 0.9*r, 0.41*r), (0.21*r, 0.9*r, 0.41*r), (0.05*r, 0.9*r, 0.4*r), (0, 0.9*r, 0.4*r), (0.029*r, 0.9*r, 0.33*r), (0.048*r, 0.9*r, 0.22*r), (0.055*r, 0.9*r, 0.16*r), (0.15*r, 0.9*r, 0.272*r), (0.12*r, 0.9*r, 0.27*r), (0.35*r, 0.9*r, 0.1*r), (0.29*r, 0.9*r, -0.15*r), (0.16*r, 0.9*r, -0.21*r), (0.1*r, 0.9*r, -0.2*r)] )
        cvArrow3 = cmds.curve(n=ctrlName+"_CvArrow3", d=3, p=[(-0.1*r, -0.9*r, 0.2*r), (-0.1*r, -0.9*r, 0.23*r), (-0.1*r, -0.9*r, 0.27*r), (-0.1*r, -0.9*r, 0.29*r), (-0.1*r, -0.9*r, 0.3*r), (-0.372*r, -0.9*r, 0.24*r), (-0.45*r, -0.9*r, -0.13*r), (-0.18*r, -0.9*r, -0.345*r), (-0.17*r, -0.9*r, -0.31*r), (-0.26*r, -0.9*r, -0.41*r), (-0.21*r, -0.9*r, -0.41*r), (-0.05*r, -0.9*r, -0.4*r), (0, -0.9*r, -0.4*r), (-0.029*r, -0.9*r, -0.33*r), (-0.048*r, -0.9*r, -0.22*r), (-0.055*r, -0.9*r, -0.16*r), (-0.15*r, -0.9*r, -0.272*r), (-0.12*r, -0.9*r, -0.27*r), (-0.35*r, -0.9*r, -0.1*r), (-0.29*r, -0.9*r, 0.15*r), (-0.16*r, -0.9*r, 0.21*r), (-0.1*r, -0.9*r, 0.2*r)] )
        cvArrow4 = cmds.curve(n=ctrlName+"_CvArrow4", d=3, p=[(0.1*r, -0.9*r, -0.2*r), (0.1*r, -0.9*r, -0.23*r), (0.1*r, -0.9*r, -0.27*r), (0.1*r, -0.9*r, -0.29*r), (0.1*r, -0.9*r, -0.3*r), (0.372*r, -0.9*r, -0.24*r), (0.45*r, -0.9*r, 0.13*r), (0.18*r, -0.9*r, 0.345*r), (0.17*r, -0.9*r, 0.31*r), (0.26*r, -0.9*r, 0.41*r), (0.21*r, -0.9*r, 0.41*r), (0.05*r, -0.9*r, 0.4*r), (0, -0.9*r, 0.4*r), (0.029*r, -0.9*r, 0.33*r), (0.048*r, -0.9*r, 0.22*r), (0.055*r, -0.9*r, 0.16*r), (0.15*r, -0.9*r, 0.272*r), (0.12*r, -0.9*r, 0.27*r), (0.35*r, -0.9*r, 0.1*r), (0.29*r, -0.9*r, -0.15*r), (0.16*r, -0.9*r, -0.21*r), (0.1*r, -0.9*r, -0.2*r)] )
        cvArrow5 = cmds.curve(n=ctrlName+"_CvArrow5", d=1, p=[(0, 0, 1.2*r), (0.09*r, 0, 1*r), (-0.09*r, 0, 1*r), (0, 0, 1.2*r)] )
        cvArrow6 = cmds.curve(n=ctrlName+"_CvArrow6", d=1, p=[(0, 0, 1.2*r), (0, 0.09*r, 1*r), (0, -0.09*r, 1*r), (0, 0, 1.2*r)] )
        # rename curveShape:
        locArrowList = [cvLoc, cvArrow1, cvArrow2, cvArrow3, cvArrow4, cvArrow5, cvArrow6]
        self.renameShape(locArrowList)
        # create ball curve:
        cvTemplateBall = self.cvControl("Ball", ctrlName+"_CvBall", r=0.7*r, d=3)
        # parent shapes to transform:
        locCtrl = cmds.group(name=ctrlName, empty=True)
        ballChildrenList = cmds.listRelatives(cvTemplateBall, shapes=True, children=True)
        for ballChildren in ballChildrenList:
            cmds.setAttr(ballChildren+".template", 1)
        self.transferShape(True, False, cvTemplateBall, [locCtrl])
        for transform in locArrowList:
            self.transferShape(True, False, transform, [locCtrl])
        # set rotation direction:
        cmds.setAttr(locCtrl+".rotateX", rot[0])
        cmds.setAttr(locCtrl+".rotateY", rot[1])
        cmds.setAttr(locCtrl+".rotateZ", rot[2])
        cmds.makeIdentity(locCtrl, rotate=True, apply=True)
        if guide:
            self.addGuideAttrs(locCtrl)
        cmds.select(clear=True)
        return locCtrl
    
    
    def cvCharacter(self, ctrlType, ctrlName, r=1, d=1, dir="+Y", rot=(0, 0, 0), *args):
        """ Create and return a curve to be used as a control.
        """
        # get radius by checking linear unit
        r = self.dpCheckLinearUnit(r)
        curve = self.cvControl(ctrlType, ctrlName, r, d, dir, rot)
        # edit a minime curve:
        cmds.addAttr(curve, longName="rigScale", attributeType='float', defaultValue=1, keyable=True, minValue=0.001)
        cmds.addAttr(curve, longName="rigScaleMultiplier", attributeType='float', defaultValue=1, keyable=False)
        
        # create Option_Ctrl Text:
        try:
            optCtrlTxt = cmds.group(name="Option_Ctrl_Txt", empty=True)
            cvText = cmds.textCurves(name="Option_Ctrl_Txt_TEMP_Grp", text="Option Ctrl", constructionHistory=False)[0]
            txtShapeList = cmds.listRelatives(cvText, allDescendents=True, type='nurbsCurve')
            if txtShapeList:
                for s, shape in enumerate(txtShapeList):
                    # store CV world position
                    curveCVList = cmds.getAttr(shape+'.cp', multiIndices=True)
                    vtxWorldPosition = []
                    for i in curveCVList :
                        cvPointPosition = cmds.xform(shape+'.cp['+str(i)+']', query=True, translation=True, worldSpace=True) 
                        vtxWorldPosition.append(cvPointPosition)
                    # parent the shapeNode :
                    cmds.parent(shape, optCtrlTxt, r=True, s=True)
                    # restore the shape world position
                    for i in curveCVList:
                        cmds.xform(shape+'.cp['+str(i)+']', a=True, worldSpace=True, t=vtxWorldPosition[i])
                    cmds.rename(shape, optCtrlTxt+"Shape"+str(s))
            cmds.delete(cvText)
            cmds.parent(optCtrlTxt, curve)
            cmds.setAttr(optCtrlTxt+".template", 1)
            cmds.setAttr(optCtrlTxt+".tx", -0.72*r)
            cmds.setAttr(optCtrlTxt+".ty", 1.1*r)
        except:
            # it will pass if we don't able to find the font to create the text
            pass
        return curve


    def findHistory(self, objList, historyName, *args):
        """Search and return the especific history of the listed objects.
        """
        if objList:
            foundHistoryList = []
            for objName in objList:
                # find historyName in the object's history:
                histList = cmds.listHistory(objName)
                for hist in histList:
                    histType = cmds.objectType(hist)
                    if histType == historyName:
                        foundHistoryList.append(hist)
            return foundHistoryList
    
    
    def cvBaseGuide(self, ctrlName, r=1, *args):
        """Create a control to be used as a Base Guide control.
            Returns the main control (circle) and the radius control in a list.
        """
        # get radius by checking linear unit
        r = self.dpCheckLinearUnit(r)
        # create a simple circle curve:
        circle = cmds.circle(n=ctrlName, ch=True, o=True, nr=(0, 0, 1), d=3, s=8, radius=r)[0]
        radiusCtrl = cmds.circle(n=ctrlName+"_RadiusCtrl", ch=True, o=True, nr=(0, 1, 0), d=3, s=8, radius=(r/4.0))[0]
        # rename curveShape:
        self.renameShape([circle, radiusCtrl])
        # configure system of limits and radius:
        cmds.setAttr(radiusCtrl+".translateX", r)
        cmds.parent(radiusCtrl, circle, relative=True)
        cmds.transformLimits(radiusCtrl, tx=(0.01, 1), etx=(True, False))
        self.setLockHide([radiusCtrl], ['ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'ro'])
        # find makeNurbCircle history of the circles:
        historyList = self.findHistory([circle, radiusCtrl], 'makeNurbCircle')
        circleHistory     = historyList[0]
        radiusCtrlHistory = historyList[1]
        # rename and make a connection for circle:
        circleHistory = cmds.rename(circleHistory, circle+"_makeNurbCircle")
        cmds.connectAttr(radiusCtrl+".tx", circleHistory+".radius", force=True)
        radiusCtrlHistory = cmds.rename(radiusCtrlHistory, radiusCtrl+"_makeNurbCircle")
        # create a mutiplyDivide in order to automatisation the radius of the radiusCtrl:
        radiusCtrlMD = cmds.createNode('multiplyDivide', name=radiusCtrl+'_MD')
        cmds.connectAttr(radiusCtrl+'.translateX', radiusCtrlMD+'.input1X', force=True)
        cmds.setAttr(radiusCtrlMD+'.input2X', 0.15)
        cmds.connectAttr(radiusCtrlMD+".outputX", radiusCtrlHistory+".radius", force=True)
        # colorize curveShapes:
        self.colorShape([circle], 'yellow')
        self.colorShape([radiusCtrl], 'cyan')
        cmds.setAttr(circle+"0Shape.lineWidth", 2)
        cmds.select(clear=True)
        # pinGuide:
        self.createPinGuide(circle)
        return [circle, radiusCtrl]
    
    
    def setAndFreeze(nodeName="", tx=None, ty=None, tz=None, rx=None, ry=None, rz=None, sx=None, sy=None, sz=None, freeze=True):
        """This function set attribute values and do a freezeTransfomation.
        """
        if nodeName != "":
            attrNameList  = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']
            attrValueList = [tx, ty, tz, rx, ry, rz, sx, sy, sz]
            # setting attribute values:
            for v, attrValue in enumerate(attrValueList):
                if attrValue:
                    try:
                        cmds.setAttr(nodeName+'.'+attrNameList[v], attrValue)
                    except:
                        pass
            # looking the need of freeze:
            if freeze:
                freezeT = False
                freezeR = False
                freezeS = False
                if tx != None or ty != None or tz != None:
                    freezeT = True
                if rx != None or ry != None or rz != None:
                    freezeR = True
                if sx != None or sy != None or sz != None:
                    freezeS = True
                try:
                    cmds.makeIdentity(nodeName, apply=freeze, translate=freezeT, rotate=freezeR, scale=freezeS)
                except:
                    pass
    
    
    def copyAttr(self, sourceItem=False, attrList=False, verbose=False, *args):
        """ Get and store in a dictionary the attributes from sourceItem.
            Returns the dictionary with attribute values.
        """
        # getting sourceItem:
        if not sourceItem:
            selList = cmds.ls(selection=True, long=True)
            if selList:
                sourceItem = selList[0]
            else:
                print(self.dpUIinst.lang["e015_selectToCopyAttr"])
        if cmds.objExists(sourceItem):
            if not attrList:
                # getting channelBox selected attributes:
                currentAttrList = cmds.channelBox('mainChannelBox', query=True, selectedMainAttributes=True)
                if not currentAttrList:
                    # list all attributes if nothing is selected:
                    currentAttrList = cmds.listAttr(sourceItem, visible=True, keyable=True)
                attrList = currentAttrList
            if attrList:
                # store attribute values in a dic:
                self.attrValueDic = {}
                for attr in attrList:
                    if cmds.objExists(sourceItem+'.'+attr):
                        value = cmds.getAttr(sourceItem+'.'+attr)
                        self.attrValueDic[attr] = value
                if verbose:
                    print(self.dpUIinst.lang["i125_copiedAttr"])
        return self.attrValueDic
    
    
    def pasteAttr(self, destinationList=False, verbose=False, *args):
        """ Get to destination list and set the dictionary values on them.
        """
        # getting destinationList:
        if not destinationList:
            destinationList = cmds.ls(selection=True, long=True)
        if destinationList and self.attrValueDic:
            # set dic values to destinationList:
            for destItem in destinationList:
                for attr in self.attrValueDic:
                    try:
                        cmds.setAttr(destItem+'.'+attr, self.attrValueDic[attr])
                    except:
                        try:
                            cmds.setAttr(destItem+'.'+attr, self.attrValueDic[attr], type='string')
                        except:
                            pass
                            if verbose:
                                print(self.dpUIinst.lang["e016_notPastedAttr"], attr)
            if verbose:
                print(self.dpUIinst.lang["i126_pastedAttr"])
    
    
    def copyAndPasteAttr(self, verbose=False, *args):
        """ Call copy and past functions.
        """
        # copy attributes and store them in the dictionary:
        self.copyAttr()
        # get destinationList:
        currentSelectedList = cmds.ls(selection=True, long=True)
        if currentSelectedList:
            if len(currentSelectedList) > 1:
                destinationList = currentSelectedList[1:]
                # calling function to paste attributes to destinationList:
                self.pasteAttr(destinationList, verbose)
    
    
    def transferAttr(self, sourceItem, destinationList, attrList, *args):
        """ Transfer attributes from sourceItem to destinationList.
        """
        if sourceItem and destinationList and attrList:
            self.copyAttr(sourceItem, attrList)
            self.pasteAttr(destinationList)
    
    
    def transferShape(self, deleteSource=False, clearDestinationShapes=True, sourceItem=None, destinationList=None, keepColor=True, force=False, *args):
        """ Transfer control shape from sourceItem to destination list
        """
        if not sourceItem:
            selList = cmds.ls(selection=True, type="transform")
            if selList and len(selList) > 1:
                # get first selected item
                sourceItem = selList[0]
                # get other selected items
                destinationList = selList[1:]
        if sourceItem:
            sourceShapeList = cmds.listRelatives(sourceItem, shapes=True, type="nurbsCurve", fullPath=True)
            if sourceShapeList:
                if destinationList:
                    for destTransform in destinationList:
                        needKeepVis = False
                        sourceVis = None
                        defList = False
                        dupSourceItem = cmds.duplicate(sourceItem)[0]
                        if keepColor:
                            self.setSourceColorOverride(dupSourceItem, [destTransform])
                        destShapeList = cmds.listRelatives(destTransform, shapes=True, type="nurbsCurve", fullPath=True)
                        if destShapeList:
                            for destShape in destShapeList:
                                # keep visibility connections if exists:
                                visConnectList = cmds.listConnections(destShape+".visibility", destination=False, source=True, plugs=True)
                                if visConnectList:
                                    needKeepVis = True
                                    sourceVis = visConnectList[0]
                                    break
                            for destShape in destShapeList:
                                # keep deformers if exists
                                try:
                                    defList = cmds.findDeformers(destShape)
                                    break
                                except:
                                    pass
                            if clearDestinationShapes:
                                cmds.delete(destShapeList)
                        # hack: unparent destination children in order to get a good shape hierarchy order as index 0:
                        destChildrenList = cmds.listRelatives(destTransform, shapes=False, type="transform", fullPath=True)
                        if destChildrenList:
                            self.destChildrenGrp = cmds.group(destChildrenList, name="dpTemp_DestChildren_Grp")
                            cmds.parent(self.destChildrenGrp, world=True)
                        if defList:
                            dpUtils.reapplyDeformers(dupSourceItem, defList)
                        dupSourceShapeList = cmds.listRelatives(dupSourceItem, shapes=True, type="nurbsCurve", fullPath=True)
                        for dupSourceShape in dupSourceShapeList:
                            if needKeepVis:
                                cmds.connectAttr(sourceVis, dupSourceShape+".visibility", force=True)
                            if not force:
                                cmds.parent(dupSourceShape, destTransform, relative=True, shape=True)
                            else:
                                # make sure we use the current shape of a froze transform, usefull to mirror control shapes
                                forcedShape = cmds.parent(dupSourceShape, destTransform, absolute=True, shape=True)[0]
                                forcedTransform = cmds.listRelatives(forcedShape, parent=True, type="transform")
                                cmds.makeIdentity(forcedTransform, apply=True, translate=True, rotate=True, scale=True)
                                cmds.parent(forcedShape, destTransform, relative=True, shape=True)
                                cmds.delete(forcedTransform)
                                if defList:
                                    if cmds.objExists(forcedShape):
                                        histList = cmds.listHistory(forcedShape)
                                        if histList:
                                            for defNode in histList:
                                                if cmds.objExists(defNode):
                                                    if cmds.objectType(defNode) == "transformGeometry":
                                                        cmds.delete(forcedShape, constructionHistory=True)
                                                        dpUtils.reapplyDeformers(destTransform+"|"+forcedShape, defList)
                                                        break
                        cmds.delete(dupSourceItem)
                        self.renameShape([destTransform])
                        # restore children transforms to correct parent hierarchy:
                        if destChildrenList:
                            cmds.parent((cmds.listRelatives(self.destChildrenGrp, shapes=False, type="transform", fullPath=True)), destTransform)
                            cmds.delete(self.destChildrenGrp)
                    if deleteSource:
                        # update cvControls attributes:
                        self.transferAttr(sourceItem, destinationList, ["className", "size", "degree", "cvRotX", "cvRotY", "cvRotZ"])
                        cmds.delete(sourceItem)
    
    
    def setSourceColorOverride(self, sourceItem, destinationList, *args):
        """ Check if there's a colorOverride for destination shapes
            and try to set it to source shapes.
        """
        colorList = []
        for item in destinationList:
            childShapeList = cmds.listRelatives(item, shapes=True, type="nurbsCurve", fullPath=True)
            if childShapeList:
                for childShape in childShapeList:
                    if cmds.getAttr(childShape+".overrideEnabled") == 1:
                        if cmds.getAttr(childShape+".overrideRGBColors") == 1:
                            colorList.append(cmds.getAttr(childShape+".overrideColorR"))
                            colorList.append(cmds.getAttr(childShape+".overrideColorG"))
                            colorList.append(cmds.getAttr(childShape+".overrideColorB"))
                            self.colorShape([sourceItem], colorList, True)
                        else:
                            colorList.append(cmds.getAttr(childShape+".overrideColor"))
                            self.colorShape([sourceItem], colorList[0])
                        break
                        
    
    def resetCurve(self, changeDegree=False, transformList=False, *args):
        """ Read the current curve degree of selected curve controls and change it to another one.
            1 to 3
            or
            3 to 1.
        """
        if not transformList:
            transformList = cmds.ls(selection=True, type="transform")
        if transformList:
            for item in transformList:
                if cmds.objExists(item+"."+DPCONTROL) and cmds.getAttr(item+"."+DPCONTROL) == 1:
                    # getting current control values from stored attributes:
                    curType = cmds.getAttr(item+".className")
                    curSize = cmds.getAttr(item+".size")
                    curDegree = cmds.getAttr(item+".degree")
                    curDir = cmds.getAttr(item+".direction")
                    curRotX = cmds.getAttr(item+".cvRotX")
                    curRotY = cmds.getAttr(item+".cvRotY")
                    curRotZ = cmds.getAttr(item+".cvRotZ")
                    if changeDegree:
                        # changing current curve degree:
                        if curDegree == 1: #linear
                            curDegree = 3 #cubic
                        else: #cubic
                            curDegree = 1 #linear
                        cmds.setAttr(item+".degree", curDegree)
                    curve = self.cvControl(curType, "Temp_Ctrl", curSize, curDegree, curDir, (curRotX, curRotY, curRotZ), 1)
                    self.transferShape(deleteSource=True, clearDestinationShapes=True, sourceItem=curve, destinationList=[item], keepColor=True)
            cmds.select(transformList)
    

    def confirmAskUser(self, titleText, messageText, *args):
        """
        """
        # ask user to continue
        resultQuestion = cmds.confirmDialog(
                                        title=titleText,
                                        message=messageText, 
                                        button=[self.dpUIinst.lang['i071_yes'], self.dpUIinst.lang['i072_no']], 
                                        defaultButton=self.dpUIinst.lang['i071_yes'], 
                                        cancelButton=self.dpUIinst.lang['i072_no'], 
                                        dismissString=self.dpUIinst.lang['i072_no'])
        if resultQuestion == self.dpUIinst.lang['i071_yes']:
            return True
        return False
    
    def dpCreateControlsPreset(self, *args):
        """ Creates a json file as a Control Preset and returns it.
        """
        resultString = None
        ctrlList, ctrlIDList = [], []
        allTransformList = cmds.ls(selection=False, type='transform')
        for item in allTransformList:
            if cmds.objExists(item+"."+DPCONTROL):
                if cmds.getAttr(item+"."+DPCONTROL) == 1:
                    ctrlList.append(item)
        if ctrlList:
            resultDialog = cmds.promptDialog(
                                            title=self.dpUIinst.lang['i129_createPreset'],
                                            message=self.dpUIinst.lang['i130_presetName'],
                                            button=[self.dpUIinst.lang['i131_ok'], self.dpUIinst.lang['i132_cancel']],
                                            defaultButton=self.dpUIinst.lang['i131_ok'],
                                            cancelButton=self.dpUIinst.lang['i132_cancel'],
                                            dismissString=self.dpUIinst.lang['i132_cancel'])
            if resultDialog == self.dpUIinst.lang['i131_ok']:
                resultName = cmds.promptDialog(query=True, text=True)
                resultName = resultName[0].upper()+resultName[1:]
                confirmSameName = True
                if resultName in self.presetDic:
                    confirmSameName = self.confirmAskUser(self.dpUIinst.lang['i129_createPreset'], self.dpUIinst.lang['i135_existingName'])
                if confirmSameName:
                    author = getpass.getuser()
                    date = str(datetime.datetime.now().date())
                    resultString = '{"_preset":"'+resultName+'","_author":"'+author+'","_date":"'+date+'","_updated":"'+date+'"'
                    # add default keys to dict:
                    ctrlIDList.append("_preset")
                    ctrlIDList.append("_author")
                    ctrlIDList.append("_date")
                    ctrlIDList.append("_updated")
                    # get all existing controls info
                    for ctrlNode in ctrlList:
                        ctrl_ID = cmds.getAttr(ctrlNode+".controlID")
                        if ctrl_ID.startswith("id_"):
                            if not ctrl_ID in ctrlIDList:
                                ctrlIDList.append(ctrl_ID)
                                ctrl_Type = cmds.getAttr(ctrlNode+".className")
                                ctrl_Degree = cmds.getAttr(ctrlNode+".degree")
                                resultString += ',"'+ctrl_ID+'":{"type":"'+ctrl_Type+'","degree":'+str(ctrl_Degree)+'}'
                    # check if we got all controlIDs:
                    for j, pID in enumerate(self.dpUIinst.ctrlPreset):
                        if not pID in ctrlIDList:
                            # get missing controlIDs from current preset:
                            resultString += ',"'+pID+'":{"type":"'+self.dpUIinst.ctrlPreset[pID]["type"]+'","degree":'+str(self.dpUIinst.ctrlPreset[pID]["degree"])+'}'
                    resultString += "}"
        return resultString
    
    
    def dpCheckLinearUnit(self, origRadius, defaultUnit="centimeter", *args):
        """ Verify if the Maya linear unit is in Centimeter.
            Return the radius to the new unit size.

            WIP!
            Changing to shapeSize cluster setup
        """
        newRadius = origRadius
    #    newRadius = 1
    #    linearUnit = cmds.currentUnit(query=True, linear=True, fullName=True)
    #    # centimeter
    #    if linearUnit == defaultUnit:
    #        newRadius = origRadius
    #    elif linearUnit == "meter":
    #        newRadius = origRadius*0.01
    #    elif linearUnit == "millimeter":
    #        newRadius = origRadius*10
    #    elif linearUnit == "inch":
    #        newRadius = origRadius*0.393701
    #    elif linearUnit == "foot":
    #        newRadius = origRadius*0.032808
    #    elif linearUnit == "yard":
    #        newRadius = origRadius*0.010936
        return newRadius
    
    
    #@dpUtils.profiler
    def shapeSizeSetup(self, transformNode, *args):
        """ Find shapes, create a cluster deformer to all and set the pivot to transform pivot.
        """
        clusterHandle = None
        childShapeList = cmds.listRelatives(transformNode, shapes=True, children=True)
    #    print("Child length {0}".format(len(childShapeList)))
        if childShapeList:
            thisNamespace = childShapeList[0].split(":")[0]
            cmds.namespace(set=thisNamespace, force=True)
            clusterName = transformNode.split(":")[1]+"_ShapeSizeCH"
            clusterHandle = cmds.cluster(childShapeList, name=clusterName)[1]
            cmds.setAttr(clusterHandle+".visibility", 0)
            cmds.xform(clusterHandle, scalePivot=(0, 0, 0), worldSpace=True)
            cmds.namespace(set=":")
        else:
            print("There are not children shape to create shapeSize setup of:", transformNode)
        if clusterHandle:
            self.connectShapeSize(clusterHandle)
    
    
    def connectShapeSize(self, clusterHandle, *args):
        """ Connect shapeSize attribute from guide main control to shapeSizeClusterHandle scale XYZ.
        """
        cmds.connectAttr(self.moduleGrp+".shapeSize", clusterHandle+".scaleX", force=True)
        cmds.connectAttr(self.moduleGrp+".shapeSize", clusterHandle+".scaleY", force=True)
        cmds.connectAttr(self.moduleGrp+".shapeSize", clusterHandle+".scaleZ", force=True)
        # re-declaring Temporary Group and parenting shapeSizeClusterHandle:
        self.dpARTempGrp = 'dpAR_Temp_Grp'
        if not cmds.objExists(self.dpARTempGrp):
            cmds.group(name=self.dpARTempGrp, empty=True)
            cmds.setAttr(self.dpARTempGrp+".visibility", 0)
            cmds.setAttr(self.dpARTempGrp+".template", 1)
            cmds.setAttr(self.dpARTempGrp+".hiddenInOutliner", 1)
            self.setLockHide([self.dpARTempGrp], ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz', 'v', 'ro'])
        cmds.parent(clusterHandle, self.dpARTempGrp)
    
    
    def addGuideAttrs(self, ctrlName, *args):
        """ Add and set attributes to this control curve be used as a guide.
        """
        # create an attribute to be used as guide by module:
        cmds.addAttr(ctrlName, longName="nJoint", attributeType='long')
        cmds.setAttr(ctrlName+".nJoint", 1)
        # colorize curveShapes:
        self.colorShape([ctrlName], 'blue')
        # shapeSize setup:
        self.shapeSizeSetup(ctrlName)
        # pinGuide:
        self.createPinGuide(ctrlName)
    
    
    def createPinGuide(self, ctrlName, *args):
        """ Add pinGuide attribute if it doesn't exist yet.
            Create a scriptJob to read this attribute change.
        """
        if not ctrlName.endswith("_JointEnd"):
            if not ctrlName.endswith("_RadiusCtrl"):
                if not cmds.objExists(ctrlName+".pinGuide"):
                    cmds.addAttr(ctrlName, longName="pinGuide", attributeType="bool")
                    cmds.setAttr(ctrlName+".pinGuide", channelBox=True)
                    cmds.addAttr(ctrlName, longName="pinGuideConstraint", attributeType="message")
                    cmds.addAttr(ctrlName, longName="lockedList", dataType="string")
                cmds.scriptJob(attributeChange=[str(ctrlName+".pinGuide"), lambda nodeName=ctrlName: self.jobPinGuide(nodeName)], killWithScene=True, compressUndo=True)
                self.jobPinGuide(ctrlName) # just forcing pinGuide setup run before wait for the job be trigger by the attribute
    
    
    def setPinnedGuideColor(self, ctrlName, status, color="red", *args):
        """ Set the color override for pinned guide shapes.
        """
        cmds.setAttr(ctrlName+".overrideEnabled", status)
        cmds.setAttr(ctrlName+".overrideColor", dic_colors[color])
        shapeList = cmds.listRelatives(ctrlName, children=True, fullPath=False, shapes=True)
        if shapeList:
            for shapeNode in shapeList:
                if status:
                    cmds.setAttr(shapeNode+".overrideEnabled", 0)
                else:
                    cmds.setAttr(shapeNode+".overrideEnabled", 1)
    
    
    def jobPinGuide(self, ctrlName, *args):
        """ Pin temporally the guide by scriptJob.
        """
        transformAttrList = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz", "v"]
        if cmds.objExists(ctrlName+".pinGuide"):
            # extracting namespace... need to find an ellegant way using message or stored attribute instead:
            nameSpaceName = None
            cmds.namespace(set=":")
            if ":" in ctrlName:
                if "|" in ctrlName:
                    nameSpaceName = ctrlName[ctrlName.rfind("|")+1:ctrlName.rfind(":")]
                else:
                    nameSpaceName = ctrlName[:ctrlName.rfind(":")]
            # work with locked attributes
            pinValue = cmds.getAttr(ctrlName+".pinGuide")
            pcName = ctrlName+"_PinGuide_PaC"
            if pinValue:
                if cmds.objExists(self.dpUIinst.tempGrp):
                    if not cmds.listConnections(ctrlName+".pinGuideConstraint", destination=False, source=True):
                        self.storeLockedList(ctrlName)
                        if nameSpaceName:
                            cmds.namespace(set=nameSpaceName)
                        for attr in transformAttrList:
                            cmds.setAttr(ctrlName+"."+attr, lock=False)
                        pc = cmds.parentConstraint(self.dpUIinst.tempGrp, ctrlName, maintainOffset=True, name=pcName)[0]
                        cmds.connectAttr(pc+".message", ctrlName+".pinGuideConstraint")
                        for attr in transformAttrList:
                            cmds.setAttr(ctrlName+"."+attr, lock=True)
            else:
                pcNodeList = cmds.listConnections(ctrlName+".pinGuideConstraint", destination=False, source=True)
                if pcNodeList:
                    cmds.delete(pcNodeList[0])
                    for attr in transformAttrList:
                        cmds.setAttr(ctrlName+"."+attr, lock=False)
                    self.restoreLockedList(ctrlName)
            self.setPinnedGuideColor(ctrlName, pinValue)
            cmds.namespace(set=":")
    
    
    def startPinGuide(self, guideBase, *args):
        """ Reload pinGuide job for already created guide.
        """
        if cmds.objExists(guideBase):
            childrenList = cmds.listRelatives(guideBase, children=True, allDescendents=True, fullPath=True, type="transform")
            if childrenList:
                for childNode in childrenList:
                    if cmds.objExists(childNode+".pinGuide"):
                        self.createPinGuide(childNode)
            if cmds.objExists(guideBase+".pinGuide"):
                self.createPinGuide(guideBase)
    
    
    def unPinGuide(self, guideBase, *args):
        """ Remove pinGuide setup.
            We expect to have the scriptJob running here to clean-up the pin setup.
        """
        if cmds.objExists(guideBase+".pinGuide"):
            cmds.setAttr(guideBase+".pinGuide", 0)


    def storeLockedList(self, ctrlName, *args):
        """ Store a string of a list of found locked attributes.
        """
        lockedAttrStr = ""
        if not cmds.objExists(ctrlName+".lockedList"):
            cmds.addAttr(ctrlName, longName="lockedList", dataType="string")
        lockedAttrList = cmds.listAttr(ctrlName, locked=True)
        if lockedAttrList:
            lockedAttrStr = ';'.join(str(e) for e in lockedAttrList)
        cmds.setAttr(ctrlName+".lockedList", lockedAttrStr, type="string")


    def restoreLockedList(self, ctrlName, *args):
        """ Lock again the stored attributes.
        """
        if cmds.objExists(ctrlName+".lockedList"):
            lockedAttr = cmds.getAttr(ctrlName+".lockedList")
            if lockedAttr:
                lockedAttrList = lockedAttr.split(";")
                if lockedAttrList:
                    for attr in lockedAttrList:
                        cmds.setAttr(ctrlName+"."+attr, lock=True)


    def importCalibration(self, *args):
        """ Import calibration from a referenced file.
            Transfer calibration for same nodes by name using calibrationList attribute.
        """
        importCalibrationNamespace = "dpImportCalibration"
        sourceRefNodeList = []
        # get user file to import calibration from
        importCalibrationPath = cmds.fileDialog2(fileMode=1, caption=self.dpUIinst.lang['i196_import']+" "+self.dpUIinst.lang['i193_calibration'])
        if not importCalibrationPath:
            return
        progressAmount = 0
        cmds.progressWindow(title=importCalibrationNamespace, progress=progressAmount, status='0% - '+self.dpUIinst.lang['i214_refFile'], isInterruptable=False)
        importCalibrationPath = next(iter(importCalibrationPath), None)
        # create a file reference:
        refFile = cmds.file(importCalibrationPath, reference=True, namespace=importCalibrationNamespace)
        refNode = cmds.file(importCalibrationPath, referenceNode=True, query=True)
        refNodeList = cmds.referenceQuery(refNode, nodes=True)
        if refNodeList:
            maxProcess = len(refNodeList)
            for item in refNodeList:
                progressAmount += 1
                cmds.progressWindow(edit=True, maxValue=maxProcess, progress=progressAmount, status=(repr(progressAmount)+' - '+self.dpUIinst.lang['i215_setAttr']))
                if cmds.objExists(item+".calibrationList"):
                    sourceRefNodeList.append(item)
        if sourceRefNodeList:
            for sourceRefNode in sourceRefNodeList:
                destinationNode = sourceRefNode[sourceRefNode.rfind(":")+1:]
                if cmds.objExists(destinationNode):
                    self.transferCalibration(sourceRefNode, [destinationNode], verbose=False)
        # remove referenced file:
        cmds.file(importCalibrationPath, removeReference=True)
        cmds.progressWindow(endProgress=True)
        print("dpImportCalibrationPath: "+importCalibrationPath)
        

    def mirrorCalibration(self, nodeName=False, fromPrefix=False, toPrefix=False, *args):
        """ Mirror calibration by naming using prefixes to find nodes.
            Ask to mirror calibration of all controls if nothing is selected.
        """
        if not fromPrefix:
            fromPrefix = cmds.textField(self.dpUIinst.allUIs["fromPrefixTF"], query=True, text=True)
            toPrefix = cmds.textField(self.dpUIinst.allUIs["toPrefixTF"], query=True, text=True)
        if fromPrefix and toPrefix:
            if not nodeName:
                currentSelectionList = cmds.ls(selection=True, type="transform")
                if currentSelectionList:
                    for selectedNode in currentSelectionList:
                        if selectedNode.startswith(fromPrefix):
                            self.mirrorCalibration(selectedNode, fromPrefix, toPrefix)
                else:
                    # ask to run for all nodes:
                    if self.confirmAskUser(self.dpUIinst.lang['m010_mirror']+" "+self.dpUIinst.lang['i193_calibration'], self.dpUIinst.lang['i042_notSelection']+"\n"+self.dpUIinst.lang['i197_mirrorAll']):
                        allNodeList = cmds.ls(fromPrefix+"*", selection=False, type="transform")
                        if allNodeList:
                            for node in allNodeList:
                                self.mirrorCalibration(node, fromPrefix, toPrefix)
            else:
                attrList = self.getCalibrationAttr(nodeName)
                if attrList:
                    destinationNode = toPrefix+nodeName[len(fromPrefix):]
                    if cmds.objExists(destinationNode):
                        self.transferAttr(nodeName, [destinationNode], attrList)
        else:
            print(self.dpUIinst.lang['i198_mirrorPrefix'])


    def transferCalibration(self, sourceItem=False, destinationList=False, attrList=False, verbose=True, *args):
        """ Transfer calibration attributes.
        """
        if not sourceItem:
            # check current selection:
            currentSelectionList = cmds.ls(selection=True, type="transform")
            if currentSelectionList:
                if len(currentSelectionList) > 1:
                    sourceItem = currentSelectionList[0]
                    destinationList = currentSelectionList[1:]
        if sourceItem:
            if not attrList:
                attrList = self.getCalibrationAttr(sourceItem)
            if attrList:
                self.transferAttr(sourceItem, destinationList, attrList)
            if verbose:
                print(self.dpUIinst.lang['i195_transferedCalib'], sourceItem, destinationList, attrList)
        else:
            print(self.dpUIinst.lang['i042_notSelection'])


    def setCalibrationAttr(self, nodeName, attrList, *args):
        """ Set the calibration attribute that contains a list of attributes to be used in the transfer calibration.
            Add calibrationList attribute if it doesn't exists.
        """
        if cmds.objExists(nodeName):
            if attrList:
                calibrationAttr = ';'.join(attrList)
                if not cmds.objExists(nodeName+".calibrationList"):
                    cmds.addAttr(nodeName, longName="calibrationList", dataType="string")
                cmds.setAttr(nodeName+".calibrationList", calibrationAttr, type="string")


    def getCalibrationAttr(self, nodeName, *args):
        """ Return the calibrationList attribute if it exists in the given nodeName.
        """
        if cmds.objExists(nodeName+".calibrationList"):
            return list(cmds.getAttr(nodeName+".calibrationList").split(";"))

    
    def getControlList(self, *args):
        """ List all dpControl transforms that has active .dpControl attribute.
            Returns a list of them.
        """
        nodeList = []
        allList = cmds.ls(selection=False, type="transform")
        if allList:
            for item in allList:
                if cmds.objExists(item+"."+DPCONTROL) and cmds.getAttr(item+"."+DPCONTROL):
                    nodeList.append(item)
        return nodeList


    def exportShape(self, nodeList=None, path=None, publish=False, dpSnapshotGrp="dpSnapshot_Grp", keepSnapshot=False, overrideExisting=True, ui=True, *args):
        """ Export control shapes from a given list or all found dpControl transforms in the scene.
            It will save a Maya ASCII file with the control shapes snapshots.
            If there is no given path, it will ask user where to save the file.
            If publish is True, it will use the current location and create the dpShapeIO directory by default.
            If keepSnapshot is True, it will parent a backup dpSnapshotGrp group to Wip_Grp and hide it.
            If overrideExisting is True, it will delete the old node before create the new snapshot.
        """
        currentPath = cmds.file(query=True, sceneName=True)
        if not currentPath:
            print(self.dpUIinst.lang['i201_saveScene'])
            return
        
        if not nodeList:
            nodeList = self.getControlList()
        if nodeList:
            if not path:
                if publish:
                    dpFolder = currentPath[:currentPath.rfind("/")+1]+self.dpUIinst.dpData+"/"+self.dpUIinst.dpShape
                    if not os.path.exists(dpFolder):
                        os.makedirs(dpFolder)
                    path = dpFolder+"/"+self.dpUIinst.dpShape+"_"+currentPath[currentPath.rfind("/")+1:]
                else:
                    pathList = cmds.fileDialog2(fileMode=0, caption="Export Shapes")
                    if pathList:
                        path = pathList[0] 
            if path:
                if ui:
                    # Starting progress window
                    progressAmount = 0
                    cmds.progressWindow(title=self.dpUIinst.lang['i164_export'], progress=progressAmount, status=self.doingName+': 0%', isInterruptable=False)
                    maxProcess = len(nodeList)
                # make sure we save the file as mayaAscii
                if not path.endswith(".ma"):
                    path = path.replace(".*", ".ma")
                cmds.undoInfo(openChunk=True)
                if not cmds.objExists(dpSnapshotGrp):
                    cmds.group(name=dpSnapshotGrp, empty=True)
                for item in nodeList:
                    if ui:
                        # Update progress window
                        progressAmount += 1
                        cmds.progressWindow(edit=True, maxValue=maxProcess, progress=progressAmount, status=(self.doingName+': ' + repr(progressAmount) + ' Shape'))
                    snapshotName = item+SNAPSHOT_SUFFIX
                    if cmds.objExists(snapshotName):
                        if overrideExisting:
                            cmds.delete(snapshotName)
                    dup = cmds.duplicate(item, name=snapshotName)[0]
                    cmds.setAttr(dup+".dpControl", 0)
                    dupChildList = cmds.listRelatives(dup, allDescendents=True, children=True, fullPath=True)
                    if dupChildList:
                        toDeleteList = []
                        for childNode in dupChildList:
                            if not cmds.objectType(childNode) == "nurbsCurve":
                                toDeleteList.append(childNode)
                        if toDeleteList:
                            cmds.delete(toDeleteList)
                    cmds.parent(dup, dpSnapshotGrp)
                # export shapes
                if cmds.listRelatives(dpSnapshotGrp, allDescendents=True, children=True, type="nurbsCurve"):
                    cmds.select(dpSnapshotGrp)
                    cmds.file(rename=path)
                    cmds.file(exportSelected=True, type='mayaAscii', prompt=False, force=True)
                    cmds.file(rename=currentPath)
                    # DEV helper keepSnapshot
                    if not cmds.objExists("WIP_Grp"): #TODO need to be refactory to get this node by masterGrp attribute
                        keepSnapshot = False
                    if keepSnapshot:
                        try:
                            cmds.parent(dpSnapshotGrp, "WIP_Grp")
                            cmds.setAttr(dpSnapshotGrp+".visibility", 0)
                            if cmds.objExists("Backup_"+dpSnapshotGrp):
                                cmds.delete("Backup_"+dpSnapshotGrp)
                            cmds.rename(dpSnapshotGrp, "Backup_"+dpSnapshotGrp)
                        except:
                            pass
                    else:
                        cmds.delete(dpSnapshotGrp)
                    print('Exported shapes to: {0}'.format(path))
                cmds.undoInfo(closeChunk=True)
        else:
            print(self.dpUIinst.lang['i202_noControls'])
        if ui:
            # Close progress window
            cmds.progressWindow(endProgress=True)


    def importShape(self, nodeList=None, path=None, recharge=False, ui=True, *args):
        """ Import control shapes from an external loaded Maya file.
            If not get an user defined parameter for a node list, it will import all shapes.
            If the recharge parameter is True, it will use the default path as current location inside dpShapeIO directory.
        """
        importShapeNamespace = "dpImportShape"
        if not nodeList:
            nodeList = self.getControlList()
        if nodeList:
            if recharge:
                currentPath = cmds.file(query=True, sceneName=True)
                if not currentPath:
                    print(self.dpUIinst.lang['i201_saveScene'])
                    return
                dpFolder = currentPath[:currentPath.rfind("/")+1]+self.dpUIinst.dpData+"/"+self.dpUIinst.dpShape
                dpShapeFile = "/"+self.dpUIinst.dpShape+"_"+currentPath[currentPath.rfind("/")+1:]
                path = dpFolder+dpShapeFile
                if not os.path.exists(path):
                    print (self.dpUIinst.lang['i202_noControls'])
                    return
            elif not path:
                pathList = cmds.fileDialog2(fileMode=1, caption="Import Shapes")
                if pathList:
                    path = pathList[0]
            if path:
                if not os.path.exists(path):
                    print(self.dpUIinst.lang['e004_objNotExist']+path)
                else:
                    # create a file reference:
                    cmds.file(path, reference=True, namespace=importShapeNamespace)
                    refNode = cmds.file(path, referenceNode=True, query=True)
                    refNodeList = cmds.referenceQuery(refNode, nodes=True)
                    if refNodeList:
                        if ui:
                            # Starting progress window
                            progressAmount = 0
                            cmds.progressWindow(title=self.dpUIinst.lang['i196_import'], progress=progressAmount, status=self.doingName+': 0%', isInterruptable=False)
                            maxProcess = len(refNodeList)
                        for sourceRefNode in refNodeList:
                            if ui:
                                # Update progress window
                                progressAmount += 1
                                cmds.progressWindow(edit=True, maxValue=maxProcess, progress=progressAmount, status=(self.doingName+': ' + repr(progressAmount) + ' Shape'))
                            if cmds.objectType(sourceRefNode) == "transform":
                                destinationNode = sourceRefNode[sourceRefNode.rfind(":")+1:-len(SNAPSHOT_SUFFIX)] #removed namespace before ":"" and the suffix _Snapshot_Crv (-13)
                                if cmds.objExists(destinationNode):
                                    self.transferShape(deleteSource=False, clearDestinationShapes=True, sourceItem=sourceRefNode, destinationList=[destinationNode], keepColor=False)
                    # remove referenced file:
                    cmds.file(path, removeReference=True)
                    print("Imported shapes: {0}".format(path))
        else:
            print(self.dpUIinst.lang['i202_noControls'])
        if ui:
            # Close progress window
            cmds.progressWindow(endProgress=True)


    def createCorrectiveJointCtrl(self, jcrName, correctiveNet, type='id_092_Correctives', radius=1, degree=3, *args):
        """ Create a corrective joint controller.
            Connect setup nodes and add calibration attributes to it.
            Returns the corrective controller and its highest zero out group.
        """
        calibrateAttrList = ["T", "R", "S"]
        calibrateAxisList = ["X", "Y", "Z"]
        toCalibrationList = []
        jcrCtrl = self.cvControl(type, jcrName.replace("_Jcr", "_Ctrl"), r=radius, d=degree, corrective=True)
        jcrGrp0 = dpUtils.zeroOut([jcrCtrl])[0]
        jcrGrp1 = dpUtils.zeroOut([jcrGrp0])[0]
        cmds.delete(cmds.parentConstraint(jcrName, jcrGrp1, maintainOffset=False))
        cmds.parentConstraint(cmds.listRelatives(jcrName, parent=True)[0], jcrGrp1, maintainOffset=True, name=jcrGrp1+"_PaC")
        cmds.parentConstraint(jcrCtrl, jcrName, maintainOffset=True, name=jcrCtrl+"_PaC")
        cmds.scaleConstraint(jcrCtrl, jcrName, maintainOffset=True, name=jcrCtrl+"_ScC")
        cmds.addAttr(jcrCtrl, longName="correctiveNetwork", attributeType="message")
        cmds.addAttr(jcrCtrl, longName="inputValue", attributeType="float", defaultValue=0)
        cmds.connectAttr(correctiveNet+".message", jcrCtrl+".correctiveNetwork", force=True)
        cmds.connectAttr(correctiveNet+".outputValue", jcrCtrl+".inputValue", force=True)
        for attr in calibrateAttrList:
            for axis in calibrateAxisList:
                remapV = cmds.createNode("remapValue", name=jcrName.replace("_Jcr", "_"+attr+axis+"_RmV"))
                intensityMD = cmds.createNode("multiplyDivide", name=jcrName.replace("_Jcr", "_"+attr+axis+"_Intensity_MD"))
                cmds.connectAttr(correctiveNet+".outputStart", remapV+".inputMin", force=True)
                cmds.connectAttr(correctiveNet+".outputEnd", remapV+".inputMax", force=True)
                cmds.connectAttr(correctiveNet+".outputValue", remapV+".inputValue", force=True)
                cmds.connectAttr(jcrCtrl+".intensity", intensityMD+".input1X", force=True)
                cmds.connectAttr(remapV+".outValue", intensityMD+".input2X", force=True)
                # add calibrate attributes:
                if attr == "S":
                    scaleClp = cmds.createNode("clamp", name=jcrName.replace("_Jcr", "_"+attr+axis+"_ScaleIntensity_Clp"))
                    cmds.addAttr(jcrCtrl, longName="calibrate"+attr+axis, attributeType="float", defaultValue=1)
                    cmds.setAttr(remapV+".outputMin", 1)
                    cmds.setAttr(scaleClp+".minR", 1)
                    cmds.setAttr(scaleClp+".maxR", 1000)
                    cmds.connectAttr(intensityMD+".outputX", scaleClp+".inputR", force=True)
                    cmds.connectAttr(scaleClp+".outputR", jcrGrp0+"."+attr.lower()+axis.lower(), force=True)
                else:
                    invertMD = cmds.createNode("multiplyDivide", name=jcrName.replace("_Jcr", "_"+attr+axis+"_Invert_MD"))
                    invertCnd = cmds.createNode("condition", name=jcrName.replace("_Jcr", "_"+attr+axis+"_Invert_Cnd"))
                    cmds.setAttr(invertCnd+".secondTerm", 1)
                    cmds.setAttr(invertCnd+".colorIfTrueR", -1)
                    cmds.addAttr(jcrCtrl, longName="calibrate"+attr+axis, attributeType="float", defaultValue=0)
                    cmds.addAttr(jcrCtrl, longName="invert"+attr+axis, attributeType="bool", defaultValue=0)
                    cmds.connectAttr(intensityMD+".outputX", invertMD+".input1X", force=True)
                    cmds.connectAttr(invertCnd+".outColorR", invertMD+".input2X", force=True)
                    cmds.connectAttr(jcrCtrl+".invert"+attr+axis, invertCnd+".firstTerm", force=True)
                    cmds.connectAttr(invertMD+".outputX", jcrGrp0+"."+attr.lower()+axis.lower(), force=True)
                cmds.connectAttr(jcrCtrl+".calibrate"+attr+axis, remapV+".outputMax", force=True)
                toCalibrationList.append("calibrate"+attr+axis)
        self.setCalibrationAttr(jcrCtrl, toCalibrationList)
        return jcrCtrl, jcrGrp1
    
    
    def addCorrectiveAttrs(self, ctrlName, *args):
        """ Add and set attributes to this control curve be used as a corrective controller.
        """
        cmds.addAttr(ctrlName, longName="intensity", attributeType="float", minValue=0, defaultValue=1, maxValue=1, keyable=True)
        # create an attribute to be used as editMode by module:
        cmds.addAttr(ctrlName, longName="editMode", attributeType="bool", keyable=False)
        cmds.setAttr(ctrlName+".editMode", channelBox=True)


    def deleteOldCorrectiveJobs(self, ctrlName, *args):
        """ Try to find an existing script job already running for this corrective controller and kill it.
        """
        jobList = cmds.scriptJob(listJobs=True)
        if jobList:
            for job in jobList:
                if ctrlName in job:
                    jobNumber = int(job[:job.find(":")])
                    cmds.scriptJob(kill=jobNumber, force=True)
                    

    def createCorrectiveMode(self, ctrlName, *args):
        """ Create a scriptJob to read this attribute change.
        """
        self.deleteOldCorrectiveJobs(ctrlName)
        cmds.scriptJob(attributeChange=[str(ctrlName+".editMode"), lambda nodeName=ctrlName: self.jobCorrectiveEditMode(nodeName)], killWithScene=True, compressUndo=True)
        if cmds.getAttr(ctrlName+".editMode"):
            self.colorShape([ctrlName], 'bonina', rgb=True)
    
    
    def jobCorrectiveEditMode(self, ctrlName, *args):
        """ Edit mode to corrective control by scriptJob.
        """
        if cmds.objExists(ctrlName+".editMode"):
            editModeValue = cmds.getAttr(ctrlName+".editMode")
            if editModeValue:
                self.colorShape([ctrlName], 'bonina', rgb=True)
            else:
                shapeList = cmds.listRelatives(ctrlName, shapes=True, children=True, fullPath=True)
                if shapeList:
                    for shapeNode in shapeList:
                        cmds.setAttr(shapeNode+".overrideRGBColors", 0)
                self.setCorrectiveCalibration(ctrlName)
    
    
    def startCorrectiveEditMode(self, *args):
        """ Reload editMode job for existing corrective controllers.
        """
        transformList = cmds.ls(selection=False, type="transform")
        if transformList:
            for transformNode in transformList:
                if cmds.objExists(transformNode+".editMode"):
                    self.createCorrectiveMode(transformNode)
    
    
    def setCorrectiveCalibration(self, ctrlName, *args):
        """ Remove corrective controller editMode setup.
            Calculate the results of transformations to set the calibration attributes.
        """
        calibrateAttrList = ["T", "R", "S"]
        calibrateAxisList = ["X", "Y", "Z"]
        if cmds.objExists(ctrlName):
            dupTemp = cmds.duplicate(ctrlName, name=ctrlName+"_TEMP")[0]
            cmds.parent(dupTemp, ctrlName+"_Zero_1_Grp")
            for attr in calibrateAttrList:
                for axis in calibrateAxisList:
                    newValue = cmds.getAttr(dupTemp+"."+attr.lower()+axis.lower())
                    if attr == "S":
                        cmds.setAttr(ctrlName+"."+attr.lower()+axis.lower(), 1) #scale
                    else:
                        cmds.setAttr(ctrlName+"."+attr.lower()+axis.lower(), 0) #translate, rotate
                    cmds.setAttr(ctrlName+".calibrate"+attr+axis, newValue)
            cmds.delete(dupTemp)
            cmds.select(ctrlName)


    def displayRotateOrderAttr(self, ctrlList, *args):
        """ Set display a non keyable rotateOrder attribute in the channelBox.
        """
        if ctrlList:
            for ctrl in ctrlList:
                if cmds.objExists(ctrl+".rotateOrder"):
                    cmds.setAttr(ctrl+".rotateOrder", keyable=False, channelBox=True)


    def setSubControlDisplay(self, ctrl, subCtrl, defValue, *args):
        """ Set the shapes visibility of sub control.
        """
        if not cmds.objExists(ctrl+".subControlDisplay"):
            cmds.addAttr(ctrl, longName="subControlDisplay", attributeType="short", minValue=0, maxValue=1, defaultValue=defValue)
            cmds.setAttr(ctrl+".subControlDisplay", channelBox=True)
        subShapeList = cmds.listRelatives(subCtrl, children=True, type="shape")
        if subShapeList:
            for subShapeNode in subShapeList:
                cmds.connectAttr(ctrl+".subControlDisplay", subShapeNode+".visibility", force=True)


    def mirrorShape(self, nodeName=False, fromPrefix=False, toPrefix=False, axis=False, *args):
        """ Mirror control shape by naming using prefixes to find nodes.
            Ask to mirror control shape of all controls if nothing is selected.
        """
        if not fromPrefix:
            fromPrefix = cmds.textField(self.dpUIinst.allUIs["fromPrefixShapeTF"], query=True, text=True)
            toPrefix = cmds.textField(self.dpUIinst.allUIs["toPrefixShapeTF"], query=True, text=True)
            axis = cmds.optionMenu(self.dpUIinst.allUIs["axisShapeMenu"], query=True, value=True)
        if fromPrefix and toPrefix:
            if not nodeName:
                currentSelectionList = cmds.ls(selection=True, type="transform")
                if currentSelectionList:
                    for selectedNode in currentSelectionList:
                        if selectedNode.startswith(fromPrefix):
                            self.mirrorShape(selectedNode, fromPrefix, toPrefix, axis)
                else:
                    # ask to run for all nodes:
                    if self.confirmAskUser(self.dpUIinst.lang['m010_mirror']+" "+self.dpUIinst.lang['m067_shape'], self.dpUIinst.lang['i042_notSelection']+"\n"+self.dpUIinst.lang['i265_mirrorShapeAll']):
                        allNodeList = cmds.ls(fromPrefix+"*", selection=False, type="transform")
                        allControlList = self.getControlList()
                        if allNodeList and allControlList:
                            # Starting progress window
                            maxProcess = len(allNodeList)
                            progressAmount = 0
                            cmds.progressWindow(title=self.dpUIinst.lang['m010_mirror'], maxValue=maxProcess, progress=progressAmount, status=self.dpUIinst.lang['m067_shape'], isInterruptable=False)
                            for node in allNodeList:
                                progressAmount += 1
                                if node in allControlList:
                                    cmds.progressWindow(edit=True, progress=progressAmount, status=self.dpUIinst.lang['m067_shape']+" "+node, isInterruptable=False)                                   
                                    self.mirrorShape(node, fromPrefix, toPrefix, axis)
                                    cmds.refresh()
                        cmds.progressWindow(endProgress=True)
            else:
                if cmds.objExists(nodeName+"."+DPCONTROL) and cmds.getAttr(nodeName+"."+DPCONTROL) == 1:
                    destinationNode = toPrefix+nodeName[len(fromPrefix):]
                    if cmds.objExists(destinationNode):
                        # do mirror algorithm
                        duplicatedSource = cmds.duplicate(nodeName, name=nodeName+"_Duplicated_TEMP")[0]
                        duplicatedGrp = cmds.group(duplicatedSource, name=duplicatedSource+"_Grp")
                        mirrorShapeGrp = cmds.group(empty=True, name=duplicatedSource+"_MirrorShape_Grp")
                        cmds.parent(duplicatedGrp, mirrorShapeGrp)
                        cmds.setAttr(mirrorShapeGrp+".scale"+axis, -1)
                        self.transferShape(deleteSource=True, clearDestinationShapes=True, sourceItem=duplicatedSource, destinationList=[destinationNode], keepColor=True, force=True)
                        cmds.delete(mirrorShapeGrp)
        else:
            print(self.dpUIinst.lang['i198_mirrorPrefix'])


    def setupDefaultValues(self, resetMode=True, ctrlList=None, *args):
        """ Set or Reset control attributes to their default values.
            Ask user to run for all nodes if there aren't any selected nodes.
            Settings argument calls the window to setup each default value for selected nodes.
        """
        if not ctrlList:
            nodeToRunList = self.getSelectedControls()
            if not nodeToRunList:
                # ask to run for all nodes:
                if self.confirmAskUser(self.dpUIinst.lang['i270_defaultValues'], self.dpUIinst.lang['i042_notSelection']+"\n"+self.dpUIinst.lang['i273_runAllNodes']):
                    nodeToRunList = self.getControlList()
        else:
            nodeToRunList = self.getControlList()
        if nodeToRunList:
            if resetMode:
                self.resetPose.runValidator(False, nodeToRunList)
            else: #set default values
                for item in nodeToRunList:
                    attrList = self.resetPose.getSetupAttrList(item, self.ignoreDefaultValuesAttrList)
                    if attrList:
                        print("attrList =", attrList)
                        for attr in attrList:
                            # hack to avoid Maya limitation to edit boolean attributes
                            if not cmds.attributeQuery(attr, node=item, attributeType=True) == "bool":
                                cmds.addAttr(item+"."+attr, edit=True, defaultValue=cmds.getAttr(item+"."+attr))
    

    def getSelectedControls(self, *args):
        """ Return the intersection of all dpControls in the scene and the selected items.
        """
        return list(set(self.getControlList()) & set(cmds.ls(selection=True, type="transform")))
    

    def defaultValueEditor(self, *args):
        """ Create an UI to edit the attributes default values.
        """
        dpUtils.closeUI(self.defaultValueWindowName)
        # window
        defaultValueOption_winWidth  = 430
        defaultValueOption_winHeight = 300
        cmds.window(self.defaultValueWindowName, title=self.dpUIinst.lang['i270_defaultValues']+" "+self.dpUIinst.lang['i274_editor'], widthHeight=(defaultValueOption_winWidth, defaultValueOption_winHeight), menuBar=False, sizeable=True, minimizeButton=True, maximizeButton=False)
        # create UI layout and elements:
        dvMainLayout = cmds.columnLayout('dvMainLayout', adjustableColumn=True, columnOffset=("both", 10), parent=self.defaultValueWindowName)
        cmds.separator(style='none', height=5, parent=dvMainLayout)
        dvHeaderLayout = cmds.rowColumnLayout('dvHeaderLayout', numberOfColumns=3, columnWidth=[(1, 150), (2, 10), (3, 180)], columnAlign=[(1, 'center'), (2, 'right'), (3, 'center')], columnAttach=[(1, 'both', 5), (2, 'both', 2), (3, 'both', 5)], adjustableColumn=2, parent=dvMainLayout)
        cmds.button("editSelectedCtrlBT", label=self.dpUIinst.lang['i011_editSelected'], command=self.populateSelectedControls, parent=dvHeaderLayout)
        cmds.separator(style='none', height=30, parent=dvHeaderLayout)
        cmds.button("selectAllBT", label=self.dpUIinst.lang['m166_selAllControls'], command=partial(self.selectAllControls, True), parent=dvHeaderLayout)
        FirstCL = cmds.columnLayout('FirstSL',  adjustableColumn=True, columnOffset=("both", 10), parent=dvMainLayout)
        firstRL = cmds.rowLayout("firstRL", numberOfColumns=4, columnWidth4=(150, 100, 50, 50), height=32, columnAlign=[(1, 'left'), (2, 'left'), (3, 'left'), (4, 'left')], columnAttach=[(1, 'both', 2), (2, 'both', 2), (3, 'both', 2), (4, 'both', 2)], parent=FirstCL)
        cmds.text("controllerTxt", label=self.dpUIinst.lang['i111_controller'], font='boldLabelFont', align="center", parent=firstRL)
        cmds.text("attributeTxt", label=self.dpUIinst.lang['i275_attribute'], font='boldLabelFont', parent=firstRL)
        cmds.text("defaultTxt", label=self.dpUIinst.lang['m042_default'], font='boldLabelFont', parent=firstRL)
        cmds.text("currentTxt", label=self.dpUIinst.lang['i276_current'], font='boldLabelFont', parent=firstRL)
        cmds.separator(style='in', height=10, parent=dvMainLayout)
        self.defaultValueLayout = cmds.scrollLayout('defaultValueMainLayout', width=350, height=200, parent=dvMainLayout)
        self.dvSelectedLayout = cmds.columnLayout('dvSelectedLayout', adjustableColumn=True, columnOffset=("both", 10), parent=self.defaultValueLayout)
        self.populateSelectedControls()
        # call window
        cmds.showWindow(self.defaultValueWindowName)
        

    def populateSelectedControls(self, *args):
        """ Refresh the default value editor UI to fill it with the selected dpAR controllers.
        """
        try:
            cmds.deleteUI(self.dvSelectedLayout)
        except:
            pass
        self.dvSelectedLayout = cmds.columnLayout('dvSelectedLayout', adjustableColumn=True, columnOffset=("both", 10), parent=self.defaultValueLayout)
        ctrlList = self.getSelectedControls()
        if ctrlList:
            ctrlList.sort()
            for c, ctrl in enumerate(ctrlList):
                attrList = self.resetPose.getSetupAttrList(ctrl, self.ignoreDefaultValuesAttrList)
                if attrList:
                    for a, attr in enumerate(attrList):
                        cmds.rowLayout(numberOfColumns=4, columnWidth4=(150, 100, 50, 50), columnAlign=[(1, 'left'), (2, 'left'), (3, 'left'), (4, 'left')], columnAttach=[(1, 'both', 2), (2, 'both', 2), (3, 'both', 2), (4, 'both', 2)], parent=self.dvSelectedLayout)
                        if a == 0:
                            cmds.button(label=ctrl, command=partial(self.selectControl, ctrl, True))
                        else:
                            cmds.text(label="")
                        cmds.text(label=attr)
                        # default value
                        cmds.floatField(value=cmds.addAttr(ctrl+"."+attr, query=True, defaultValue=True), precision=3, changeCommand=partial(self.setDefaultValue, ctrl, attr))
                        # current value
                        cmds.floatField(value=cmds.getAttr(ctrl+"."+attr), precision=3, changeCommand=partial(self.setCurrentValue, ctrl, attr))
                    cmds.separator(style='in', height=10, parent=self.dvSelectedLayout)


    def selectControl(self, ctrl, refreshUI=False, *args):
        """ Select the given controller.
            Populate the defaultValueEditor if True.
        """
        if cmds.objExists(ctrl):
            cmds.select(ctrl)
        if refreshUI:
            self.populateSelectedControls()


    def selectAllControls(self, refreshUI=False, *args):
        """ Select all dpAR controllers in the scene.
            Populate the defaultValueEditor if True.
        """
        ctrlList = self.getControlList()
        if ctrlList:
            cmds.select(ctrlList)
        if refreshUI:
            self.populateSelectedControls()


    def setDefaultValue(self, ctrl, attr, value, *args):
        """ Edit the default value of the given controller.
        """
        cmds.addAttr(ctrl+"."+attr, edit=True, defaultValue=value)


    def setCurrentValue(self, ctrl, attr, value, *args):
        """ Edit the current value of the given controller.
        """
        cmds.setAttr(ctrl+"."+attr, value)


    def resetMirrorShape(self, *args):
        """ Call reset all controls before run mirrorShape script.
        """
        self.setupDefaultValues(resetMode=True, ctrlList=self.getControlList())
        self.mirrorShape()
