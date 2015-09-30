# importing libraries:
import maya.cmds as cmds
import maya.mel as mel

# global variables to this module:    
CLASS_NAME = "Biped"
TITLE = "m026_biped"
DESCRIPTION = "m027_bipedDesc"
ICON = "/Icons/dp_biped.png"


def Biped(self):
    """ This function will create all guides needed to compose a biped.
    """
    # check modules integrity:
    guideDir = 'Modules'
    checkModuleList = ['dpLimb', 'dpFoot', 'dpFinger', 'dpSpine', 'dpHead']
    checkResultList = self.startGuideModules(guideDir, "check", checkModuleList)
    
    if len(checkResultList) == 0:
        # woking with SPINE system:
        # create spine module instance:
        spineInstance = self.initGuide('dpSpine', guideDir)
        # editing spine base guide informations:
        self.guide.Spine.editUserName(spineInstance, checkText=self.langDic[self.langName]['m011_spine'].lower())
        cmds.setAttr(spineInstance.moduleGrp+".translateY", 11)
        cmds.setAttr(spineInstance.annotation+".translateY", -6)
        cmds.setAttr(spineInstance.radiusCtrl+".translateX", 2.5)
        
        # woking with HEAD system:
        # create head module instance:
        headInstance = self.initGuide('dpHead', guideDir)
        # editing head base guide informations:
        self.guide.Head.editUserName(headInstance, checkText=self.langDic[self.langName]['m017_head'].lower())
        cmds.setAttr(headInstance.moduleGrp+".translateY", 17)
        cmds.setAttr(headInstance.annotation+".translateY", 3.5)
        
        # parent head guide to spine guide:
        cmds.parent(headInstance.moduleGrp, spineInstance.cvLocator, absolute=True)
        
        # working with LEG system:
        # create leg module instance:
        legLimbInstance = self.initGuide('dpLimb', guideDir)
        # setting X mirror:
        self.guide.Limb.changeMirror(legLimbInstance, "X")
        # change limb guide to leg type:
        self.guide.Limb.changeType(legLimbInstance, self.langDic[self.langName]['m030_leg'])
        # change name to leg:
        self.guide.Limb.editUserName(legLimbInstance, checkText=self.langDic[self.langName]['m030_leg'].lower())
        cmds.setAttr(legLimbInstance.annotation+".translateY", -4)
        
        # editing leg base guide informations:
        legBaseGuide = legLimbInstance.moduleGrp
        cmds.setAttr(legBaseGuide+".type", 1)
        cmds.setAttr(legBaseGuide+".translateX", 1.5)
        cmds.setAttr(legBaseGuide+".translateY", 10)
        cmds.setAttr(legBaseGuide+".rotateX", 0)
        cmds.setAttr(legLimbInstance.radiusCtrl+".translateX", 1.5)
        
        # edit location of leg ankle guide:
        cmds.setAttr(legLimbInstance.cvExtremLoc+".translateZ", 8.5)
        
        # parent leg guide to spine base guide:
        cmds.parent(legBaseGuide, spineInstance.moduleGrp, absolute=True)
        
        # create foot module instance:
        footInstance = self.initGuide('dpFoot', guideDir)
        self.guide.Foot.editUserName(footInstance, checkText=self.langDic[self.langName]['m024_foot'].lower())
        cmds.setAttr(footInstance.annotation+".translateY", -3)
        cmds.setAttr(footInstance.moduleGrp+".translateX", 1.5)
        cmds.setAttr(footInstance.cvFootLoc+".translateZ", 1.5)
        
        # parent foot guide to leg ankle guide:
        cmds.parent(footInstance.moduleGrp, legLimbInstance.cvExtremLoc, absolute=True)
        
        # working with ARM system:
        # creating module instances:
        armLimbInstance = self.initGuide('dpLimb', guideDir)
        # setting X mirror:
        self.guide.Limb.changeMirror(armLimbInstance, "X")
        # change name to arm:
        self.guide.Limb.editUserName(armLimbInstance, checkText=self.langDic[self.langName]['m028_arm'].lower())
        cmds.setAttr(armLimbInstance.annotation+".translateX", 3)
        cmds.setAttr(armLimbInstance.annotation+".translateY", 0)
        cmds.setAttr(armLimbInstance.annotation+".translateZ", 2)
        # edit arm limb guide:
        armBaseGuide = armLimbInstance.moduleGrp
        cmds.setAttr(armBaseGuide+".translateX", 2.5)
        cmds.setAttr(armBaseGuide+".translateY", 16)
        cmds.setAttr(armBaseGuide+".displayAnnotation", 0)
        cmds.setAttr(armLimbInstance.cvExtremLoc+".translateZ", 7)
        cmds.setAttr(armLimbInstance.radiusCtrl+".translateX", 1.5)
        # parent arm guide to spine chest guide:
        cmds.parent(armLimbInstance.moduleGrp, spineInstance.cvLocator, absolute=True)
        
        # create finger instances:
        indexFingerInstance  = self.initGuide('dpFinger', guideDir)
        self.guide.Finger.editUserName(indexFingerInstance, checkText=self.langDic[self.langName]['m032_index'].lower())
        middleFingerInstance = self.initGuide('dpFinger', guideDir)
        self.guide.Finger.editUserName(middleFingerInstance, checkText=self.langDic[self.langName]['m033_middle'].lower())
        ringFingerInstance   = self.initGuide('dpFinger', guideDir)
        self.guide.Finger.editUserName(ringFingerInstance, checkText=self.langDic[self.langName]['m034_ring'].lower())
        pinkFingerInstance   = self.initGuide('dpFinger', guideDir)
        self.guide.Finger.editUserName(pinkFingerInstance, checkText=self.langDic[self.langName]['m035_pink'].lower())
        thumbFingerInstance  = self.initGuide('dpFinger', guideDir)
        self.guide.Finger.editUserName(thumbFingerInstance, checkText=self.langDic[self.langName]['m036_thumb'].lower())
        self.guide.Finger.changeJointNumber(thumbFingerInstance, 2)
        
        # edit finger guides:
        fingerInstanceList = [indexFingerInstance, middleFingerInstance, ringFingerInstance, pinkFingerInstance, thumbFingerInstance]
        fingerTZList       = [0.6, 0.2, -0.2, -0.6, 0.72]
        for n, fingerInstance in enumerate(fingerInstanceList):
            cmds.setAttr(fingerInstance.moduleGrp+".translateX", 11)
            cmds.setAttr(fingerInstance.moduleGrp+".translateY", 16)
            cmds.setAttr(fingerInstance.moduleGrp+".translateZ", fingerTZList[n])
            cmds.setAttr(fingerInstance.moduleGrp+".displayAnnotation", 0)
            cmds.setAttr(fingerInstance.radiusCtrl+".translateX", 0.3)
            cmds.setAttr(fingerInstance.annotation+".visibility", 0)
            
            if n == len(fingerInstanceList)-1:
                # correct not commun values for thumb guide:
                cmds.setAttr(thumbFingerInstance.moduleGrp+".translateX", 10.1)
                cmds.setAttr(thumbFingerInstance.moduleGrp+".nJoints", 2)
                cmds.setAttr(thumbFingerInstance.moduleGrp+".rotateX", 60)
            
            # parent finger guide to the arm wrist guide:
            cmds.parent(fingerInstance.moduleGrp, armLimbInstance.cvExtremLoc, absolute=True)
        
        # select spineGuide_base:
        cmds.select(spineInstance.moduleGrp)
    else:
        # error checking modules in the folder:
        mel.eval('error \"'+ self.langDic[self.langName]['e001_guideNotChecked'] +' - '+ (", ").join(checkResultList) +'\";')
