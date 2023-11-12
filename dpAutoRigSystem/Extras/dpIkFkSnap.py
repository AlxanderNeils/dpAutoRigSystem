###
#
#   THANKS to:
#       Renaud Lessard
#
#   Based on:
#       https://github.com/renaudll/omtk/blob/9b756fb9e822bf03b4c643328a283d29187298fd/omtk/animation/ikfkTools.py
#   
###


# importing libraries:
from maya import cmds
from maya.api import OpenMaya
from ..Modules.Library import dpControls
from ..Modules.Library import dpUtils
import math

DP_IKFKSNAP_VERSION = 2.0


####
# TEMP TO BE DELETED:
#
# global variables to this module:    
CLASS_NAME = "IkFkSnap"
TITLE = "m051_headDef"
DESCRIPTION = "m052_headDefDesc"
ICON = "/Icons/dp_AR.png"
#
#
####


class IkFkSnap(object):
    def __init__(self, dpUIinst, ui=True, *args):
        # defining variables:
        self.dpUIinst = dpUIinst
        self.ctrls = dpControls.ControlClass(self.dpUIinst)

        ###
        # WIP variables
        self.optCtrl = "Option_Ctrl"
        self.poleVector = "dpAR_1_Elbow_Ik_Ctrl"
        self.ikCtrl = "dpAR_1_Wrist_Ik_Ctrl"
        self.fkCtrlList = ["dpAR_1_Shoulder_Fk_Ctrl", "dpAR_1_Elbow_Fk_Ctrl", "dpAR_1_Wrist_Fk_Ctrl"]
        self.ikJntList = ["dpAR_1_Shoulder_Ik_Jxt", "dpAR_1_Elbow_Ik_Jxt", "dpAR_1_Wrist_Ik_Jxt"]
        self.attr = "dpAR_1Fk"
        self.clavicleCtrl = "dpAR_1_Clavicle_Ctrl"
        self.autoClavicleGrp = "dpAR_1_Clavicle_Ctrl_Grp"
        ###

        
        # store the initial ikFk extrem offset
        self.extremOffsetMatrix = self.getOffsetMatrix(self.ikCtrl, self.fkCtrlList[-1])
        
        print("self.extremOffsetMatrix = ", self.extremOffsetMatrix)


        # call main function
        if ui:
            self.dpIkFkSnapUI(self)
    

    def getOffsetMatrix(self, wm, wim, *args):
        """
        """
        aM = OpenMaya.MMatrix(cmds.getAttr(wm+".worldMatrix[0]"))
        bM = OpenMaya.MMatrix(cmds.getAttr(wim+".worldInverseMatrix[0]"))
        return (aM * bM)


    def getOffsetXform(self, wm, wim, *args):
        """
        """
        aM = OpenMaya.MMatrix(cmds.getAttr(wm+".xformMatrix"))
        bM = OpenMaya.MMatrix(cmds.getAttr(wim+".xformMatrix"))
        return (aM * bM)


    def dpCloseIkFkSnapUI(self, *args):
        if cmds.window('dpIkFkSnapWindow', query=True, exists=True):
            cmds.deleteUI('dpIkFkSnapWindow', window=True)
    
    
    def bakeAutoClavicle(self, *args):
        """
        """

        self.autoClavOffset = self.getOffsetXform(self.clavicleCtrl, self.autoClavicleGrp)
        print("self.autoClavOffset = ", self.autoClavOffset)

        cmds.xform(self.clavicleCtrl, matrix=list(self.autoClavOffset), worldSpace=False)
        cmds.xform(self.clavicleCtrl, translation=[0, 0, 0], worldSpace=False)

        #cmds.xform(self.clavicleCtrl, matrix=list(self.autoClavOffset), worldSpace=False)
        #cmds.xform(self.clavicleCtrl, translation=[0, 0, 0], worldSpace=False)
        
            
        #for attr in ['rx', 'ry', 'rz']:
        #    cmds.setAttr(self.clavicleCtrl+"."+attr, (cmds.getAttr(self.clavicleCtrl+"."+attr)+cmds.getAttr(self.autoClavicleGrp+"."+attr)))

        # Part 1: Get a MTransformationMatrix from an object for the sake of the example.
        # You can use your own MTransformationMatrix if it already exists of course.
        # get a MDagPath for our node:
#        selList = OpenMaya.MSelectionList() # make a sel list # MSelectionList
#        selList.add(self.clavicleCtrl) # add our node by name
#        mDagPath = selList.getDagPath(0) # fill the dag path with our node
        # Create a MFnTransform object for our MDagPath,
        # and extract a MTransformationMatrix from it:
#        transformFunc = OpenMaya.MFnTransform(mDagPath) # MFnTransform
#        mTransformMtx = transformFunc.transformation() # MTransformationMatrix
        #-------------------------------------------
        # Part 2, get the euler values
        # Get an MEulerRotation object
#        eulerRot = OpenMaya.MEulerRotation
#        eulerRot.add(mTransformMtx) # MEulerRotation
        # note, we *don't* have to set the rot order here...
        # Convert from radians to degrees:
#        angles = [math.degrees(angle) for angle in (eulerRot.x, eulerRot.y, eulerRot.z)]
#        print(angles, "MTransformationMatrix")


        

        

        # reset autoClavicle rotateValues to zero default



    def dpIkFkSnapUI(self, *args):
        """ Create a window in order to load the original model and targets to be mirrored.
        """
        # creating dpIkFkSnapUI Window:
        self.dpCloseIkFkSnapUI()
        ikFkSnap_winWidth  = 175
        ikFkSnap_winHeight = 75
        dpIkFkSnapWin = cmds.window('dpIkFkSnapWindow', title=" self.dpUIinst.lang['m###_ikFkSnap'] "+str(DP_IKFKSNAP_VERSION), widthHeight=(ikFkSnap_winWidth, ikFkSnap_winHeight), menuBar=False, sizeable=True, minimizeButton=False, maximizeButton=False, menuBarVisible=False, titleBar=True)

        # creating layout:
        ikFkSnapLayout = cmds.columnLayout('ikFkSnapLayout', columnOffset=("left", 30))
        cmds.separator(style='none', height=7, parent=ikFkSnapLayout)
        cmds.button(label="Fk -> iK", annotation="", width=110, backgroundColor=(0.45, 1.0, 0.6), command=self.snapFkToIk, parent=ikFkSnapLayout)
        cmds.separator(style='in', height=10, width=110, parent=ikFkSnapLayout)
        cmds.button(label="ik -> Fk", annotation="", width=110, backgroundColor=(1.0, 0.45, 0.45), command=self.snapIkToFk, parent=ikFkSnapLayout)
        
        # call dpIkFkSnapUI Window:
        cmds.showWindow(dpIkFkSnapWin)


    def snapIkToFk(self, *args):
        """
        """
        # bake autoClavicle to controller
        if cmds.getAttr(self.clavicleCtrl+".follow"):
            self.bakeAutoClavicle()



        #cmds.setAttr(self.optCtrl+"."+self.attr, 0) #ik
        followValue = cmds.getAttr(self.clavicleCtrl+".follow")
        cmds.setAttr(self.clavicleCtrl+".follow", 0)

        if not cmds.getAttr(self.fkCtrlList[0]+".follow") == 1:
            cmds.setAttr(self.fkCtrlList[0]+".follow", 1)

        for ctrl, jnt in zip(self.fkCtrlList, self.ikJntList):
            cmds.xform(ctrl, matrix=(cmds.xform(jnt, matrix=True, query=True, worldSpace=True)), worldSpace=True)

        #if followValue:
        #    cmds.setAttr(self.clavicleCtrl+".follow", followValue)
        #if fkFollowValue:
        #    cmds.setAttr(self.fkCtrlList[0]+".follow", fkFollowValue)
        cmds.setAttr(self.optCtrl+"."+self.attr, 1) #fk

    
    def snapFkToIk(self, *args):
        """
        """
        print("WIP")
        if cmds.getAttr(self.clavicleCtrl+".follow"):
            self.bakeAutoClavicle()

        followValue = cmds.getAttr(self.clavicleCtrl+".follow")
        cmds.setAttr(self.clavicleCtrl+".follow", 0)

        # extrem ctrl
        fkM = OpenMaya.MMatrix(cmds.getAttr(self.fkCtrlList[-1]+".worldMatrix[0]"))
        toIkM = self.extremOffsetMatrix * fkM
        cmds.xform(self.ikCtrl, matrix=list(toIkM), worldSpace=True)

        # poleVector ctrl
        posRef = cmds.xform(self.fkCtrlList[1], translation=True, query=True, worldSpace=True)
        posS = cmds.xform(self.fkCtrlList[0], translation=True, query=True, worldSpace=True)
        posM = posRef
        posE = cmds.xform(self.fkCtrlList[-1], translation=True, query=True, worldSpace=True)
        posRefPos = self._get_swivel_middle(posS, posM, posE)
        posDir = dpUtils.subVectors(posM, posRefPos)
        dpUtils.normalizeVector(posDir)
        fSwivelDistance = dpUtils.distanceVectors(posS, posE)
        posSwivel = dpUtils.addVectors(dpUtils.multiScalarVector(posDir, fSwivelDistance), posRef)
        #posSwivel = [posDir[0]*fSwivelDistance+posRef[0], posDir[1]*fSwivelDistance+posRef[1], posDir[2]*fSwivelDistance+posRef[2]]

        cmds.xform(self.poleVector, translation=posSwivel, worldSpace=True)
        
        #if followValue:
        #    cmds.setAttr(self.clavicleCtrl+".follow", followValue)
        cmds.setAttr(self.optCtrl+"."+self.attr, 0) #ik
        return


        # Reset footroll attributes
        if hasattr(self, 'footRollAtts'): # Hack: libSerialization don't write the attribute if it's empty wich can cause a crash
            for att in self.footRollAtts:
                att.set(0)


    def _get_swivel_middle(self, posS, posM, posE):
        fLengthS = dpUtils.distanceVectors(posM, posS)
        fLengthE = dpUtils.distanceVectors(posM, posE)
        fLengthRatio = fLengthS / (fLengthS+fLengthE)
        return dpUtils.addVectors(dpUtils.multiScalarVector(dpUtils.subVectors(posE, posS), fLengthRatio), posS)
        #return [(posE[0]-posS[0])*fLengthRatio+posS[0], (posE[1]-posS[1])*fLengthRatio+posS[1], (posE[2]-posS[2])*fLengthRatio+posS[2]]
