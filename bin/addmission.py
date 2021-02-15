from unitypack.asset import Asset
from unitypack.object import FFOrderedDict

TABLEDATA_PATH = 'CustomAssetBundle-1dca92eecee4742d985b799d8226666d'
XDTINDEX = 7

f = open(TABLEDATA_PATH, 'rb')
tabledata = Asset.from_file(f)

xdtdata = tabledata.objects[XDTINDEX].contents
missionTable = xdtdata['m_pMissionTable']
questItemTable = xdtdata['m_pQuestItemTable']

missionData = missionTable['m_pMissionData']
missionStringData = missionTable['m_pMissionStringData']
journalData = missionTable['m_pJournalData']
rewardData = missionTable['m_pRewardData']
questItemData = questItemTable['m_pItemData']
questItemStringData = questItemTable['m_pItemStringData']

# Use this to manually create and store quest items
def createQuestItem(name):
	index = len(questItemData)

	itemString = FFOrderedDict(0)
	for k,v in questItemStringData[0].items(): itemString[k] = v

	itemString['m_strName'] = name
	itemString['m_strComment'] = name
	questItemStringData.append(itemString)

	item = FFOrderedDict(0)
	for k,v in questItemData[0].items(): item[k] = v

	item['m_iIcon'] = 2 # Probably unneeded but every item has this icon
	item['m_iItemName'] = index
	item['m_iItemNumber'] = index
	item['m_iItemComment'] = index
	questItemData.append(item)

	return index

QUEST_FUSION_SAMPLE = createQuestItem("Fusion Sample")
QUEST_FUSION_DRIVE = createQuestItem("Fusion Drive")
QUEST_DON_DOOM_LEG = createQuestItem("Don Doom Leg")

# General mission data
MISSION_NAME = 'Doom\'s Day'
MISSION_TYPE = 3 # 1: guide 2: nano 3: world
MISSION_DIFFICULTY = 2 # 0: easy 1: normal 2: hard
REQUIRED_LEVEL = 4 
GIVER_ID = 776

MISSION_DESCRIPTION_TEXT = 'I have heard report of one of Fuse\'s minions terrorizing Pokey Oaks. From what I hear, this is no regular monster... this is something bigger. Are you up to help me investigate?'
MISSION_COMPLETE_SUMMARY_TEXT = 'I defeated Don Doom, Fuse\'s strongest minion.'
NPC_MISSION_COMPLETE_SUMMARY_TEXT = 'You have done well, but I am afraid Fuse\'s monsters are growing too strong. The time machine remains our only hope.'
MISSION_SUMMARY_TEXT = 'Investigate and defeat the monster ravaging Pokey Oaks.'

MISSION_COMPLETE_BARKERS = ['Thanks for taking care of that giant Doom Strider.', 'You are really brave for taking on Don Doom!', 'How much did Samurai Jack pay you to fight that big ugly Doom Strider?', 'Can I get one of your Super Slayer items?']
MISSION_PREREQS = [501] # Array of mission ids (in this case Spawn Spree)

# Task data
# Task types - 1: talk to npc 2: touch waypoint 3: interact with object 4: deliver item to npc 5: kill mobs 6: escort
TASK_DATA = [
	{
		'journalNPC': 776,
		'objective': 'Go to Pokey Oaks Mall.',
		'taskDesc': 'Investigate the area in Pokey Oaks and see if you can get a clue of what\'s going on.',
		'initialMessage': {
			'type': 2,
			'text': 'My readings show an increasing concentration of Fusion Matter near the Pokey Oaks mall. Perhaps this is what we are looking for.',
			'npc': 776,
		},
		'initialDialog': {
			'text': 'Thank you for taking on this task. I will be sure to reward you generously.',
			'npc': 776,
		},
		'successDialog': {
			'text': 'You\'ve arrived! Wonderful.',
			'npc': 776,
		},

		'taskType': 2,
		'target': 1093, 
		'waypoint': 1093, 
	},
	{
		'journalNPC': 776,
		'objective': 'Defeat nearby Fusion Spawns.',
		'taskDesc': 'See if you can get some samples from the nearby Fusion Spawns.',

		'initialMessage': {
			'type': 2,
			'text': 'We have not found the monster we were looking for, but a plethora of Fusion Spawns instead. You must take them out.',
			'npc': 776,
		},
		'successMessage': {
			'type': 2,
			'text': 'You collected some samples! Wonderful.',
			'npc': 776,
		},

		'taskType': 5,
		# You need to specify the start items for mob drop tasks otherwise the popup for the mob not dropping an item will be blank. 
		'startItems': {
			'items': [QUEST_FUSION_SAMPLE],
			'count': [0]
		},
		'mobs': [249],
		'drops': [QUEST_FUSION_SAMPLE],
		'dropRates': [65],
		'dropNum': [5]
	},
	{
		'journalNPC': 2555,
		'objective': 'Bring samples to Computress.',
		'taskDesc': 'Dexter wants to take a look at these samples. Please bring them to me in Sector V.',

		'initialMessage': {
			'type': 2,
			'text': 'You should bring those samples to Computress before you return to me.',
			'npc': 776,
		},
		'successDialog': {
			'text': "Thank you for bringing these samples here. I will give you a Fusion Drive that you can use to locate this monster.",
			'npc': 2555
		},

		'taskType': 4,
		'targetNPC': 2555,
		'startItems': {
			'items': [QUEST_FUSION_SAMPLE],
			'count': [5]
		},
		'successItems': {
			'items': [QUEST_FUSION_SAMPLE, QUEST_FUSION_DRIVE],
			'count': [-5, 1]
		}
	},
	{
		'journalNPC': 776,
		'objective': 'Bring Fusion Drive to Jack.',
		'taskDesc': 'Bring that calibrated Fusion Drive to me, quickly. This is our window of opportunity.',

		'initialMessage': {
			'type': 2,
			'text': 'You have received a Fusion Drive calibrated by these samples, but it is very unstable. Bring it here immediately.',
			'npc': 776,
		},

		'taskType': 4,
		'targetNPC': 776,
		'startItems': {
			'items': [QUEST_FUSION_DRIVE],
			'count': [1]
		},
		'successItems': {
			'items': [QUEST_FUSION_DRIVE],
			'count': [-1]
		},
		'timer': 60,
		'failTask': {
			'journalNPC': 2555,
			'objective': 'Return to Computress.',
			'taskDesc': 'The Fusion Drive has become too unstable. Bring it back to me so I can recalibrate it.',
			'initialMessage': {
				'type': 2,
				'text': 'It appears the Fusion Drive is deteriorating. Bring it back to Computress.',
				'npc': 776,
			},
			'taskType': 1,
			'targetNPC': 2555,
			'successItems': {
				'items': [QUEST_FUSION_DRIVE],
				'count': [1]
			}
		},
		'failItems': {
			'items': [QUEST_FUSION_DRIVE],
			'count': [-1]
		}
	},
	{
		'journalNPC': 776,
		'objective': 'Find and defeat Don Doom in Pokey Oaks.',
		'taskDesc': 'This monster should be in Pokey Oaks North, but it moves quickly. Look for it and hunt it down.',

		'initialMessage': {
			'type': 2,
			'text': 'Great. The drive indicates that this concentration of Fusion Matter is moving towards the north end of Pokey Oaks. That is where this monster will be.',
			'npc': 776,
		},
		'successMessage': {
			'type': 2,
			'text': 'You have done well, hero. Bring one of the legs of this wretched monster back to me, and I will reward you.',
			'npc': 776,
		},

		'taskType': 5,
		'mobs': [454],
		'mobCount': [1],
		'successItems': {
			'items': [QUEST_DON_DOOM_LEG],
			'count': [1]
		},
	},
	{
		'journalNPC': 776,
		'objective': 'Bring Don Doom leg to Jack.',
		'taskDesc': 'Bring the leg of that monster to me so I can further research it.',

		'taskType': 4,
		'targetNPC': 776,
		'startItems': {
			'items': [QUEST_DON_DOOM_LEG],
			'count': [1]
		},
		'successItems': {
			'items': [QUEST_DON_DOOM_LEG],
			'count': [-1]
		},
		
	},

]

# Reward data
REWARD_FM = 81836
REWARD_TAROS = 16384
REWARD_ITEM_TYPES = [1,2,3,0]
REWARD_ITEMS = [420,404,410,619]

def main(tabledata):
	# Helper functions

	def createMissionString(string):
		entry = FFOrderedDict(0)
		entry['m_pstrNameString'] = string

		missionStringData.append(entry)
		return len(missionStringData) - 1

	MISSION_DESCRIPTION = createMissionString(MISSION_DESCRIPTION_TEXT)
	MISSION_COMPLETE_SUMMARY = createMissionString(MISSION_COMPLETE_SUMMARY_TEXT)
	NPC_MISSION_COMPLETE_SUMMARY = createMissionString(NPC_MISSION_COMPLETE_SUMMARY_TEXT)
	MISSION_SUMMARY = createMissionString(MISSION_SUMMARY_TEXT)
	
	def createJournalEntry(taskDesc):
		entry = FFOrderedDict(0)
		for k,v in journalData[0].items(): entry[k] = v

		entry['m_iDetaileMissionDesc'] = MISSION_DESCRIPTION
		entry['m_iMissionCompleteSummary'] = MISSION_COMPLETE_SUMMARY
		entry['m_iDetaileMissionCompleteSummary'] = NPC_MISSION_COMPLETE_SUMMARY
		entry['m_iDetailedTaskDesc'] = createMissionString(taskDesc)
		entry['m_iMissionSummary'] = MISSION_SUMMARY

		journalData.append(entry)
		return len(journalData) - 1

	# Create reward
	reward = FFOrderedDict(0)
	for k,v in rewardData[0].items(): 
		reward[k] = v
		if isinstance(v, list):
			reward[k] = [0] * len(v)

	reward['m_iMissionRewardID'] = len(rewardData)
	reward['m_iCash'] = REWARD_TAROS
	reward['m_iFusionMatter'] = REWARD_FM
	for i in range(min(4, len(REWARD_ITEM_TYPES))):
		reward['m_iMissionRewarItemType'][i] = REWARD_ITEM_TYPES[i]
		reward['m_iMissionRewardItemID'][i] = REWARD_ITEMS[i]

	rewardData.append(reward)

	# Create mission
	nameId = createMissionString(MISSION_NAME)

	maxMissionId = 0
	for data in missionData:
		if data['m_iHMissionID'] > maxMissionId: 
			maxMissionId = data['m_iHMissionID']
	missionId = maxMissionId + 1

	maxTaskId = 0
	for data in missionData:
		if data['m_iHTaskID'] > maxTaskId: 
			maxTaskId = data['m_iHTaskID']
	maxTaskId = maxTaskId + 1

	lastNonInstanceTask = maxTaskId

	def addMissionData(mission, taskInfo):
		for k,v in missionData[0].items(): 
			mission[k] = v
			if isinstance(v, list):
				mission[k] = [0] * len(v)

		mission['m_iHMissionName'] = nameId
		mission['m_iHJournalNPCID'] = taskInfo['journalNPC']
		mission['m_iHMissionID'] = missionId

		mission['m_iHMissionType'] = MISSION_TYPE
		mission['m_iHDifficultyType'] = MISSION_DIFFICULTY
		mission['m_iCTRReqLvMin'] = REQUIRED_LEVEL

		mission['m_iHTaskType'] = taskInfo['taskType']
		mission['m_iHCurrentObjective'] = createMissionString(taskInfo['objective'])

		if 'initialMessage' in taskInfo:
			mission['m_iSTMessageType'] = 2
			mission['m_iSTMessageTextID'] = createMissionString(taskInfo['initialMessage']['text'])
			mission['m_iSTMessageSendNPC'] = taskInfo['initialMessage']['npc']

		if 'initialDialog' in taskInfo:
			mission['m_iSTDialogBubble'] = createMissionString(taskInfo['initialDialog']['text'])
			mission['m_iSTDialogBubbleNPCID'] = taskInfo['initialDialog']['npc']
		
		if 'successMessage' in taskInfo:
			mission['m_iSUMessageType'] = 2
			mission['m_iSUMessagetextID'] = createMissionString(taskInfo['successMessage']['text']) # lowercase t 🙄
			mission['m_iSUMessageSendNPC'] = taskInfo['successMessage']['npc']

		if 'successDialog' in taskInfo:
			mission['m_iSUDialogBubble'] = createMissionString(taskInfo['successDialog']['text'])
			mission['m_iSUDialogBubbleNPCID'] = taskInfo['successDialog']['npc']
			
		if 'startItems' in taskInfo:
			for i in range(min(3, len(taskInfo['startItems']['items']))):
				mission['m_iSTItemID'][i] = taskInfo['startItems']['items'][i]
				mission['m_iSTItemNumNeeded'][i] = taskInfo['startItems']['count'][i]
				if taskInfo['taskType'] != 5:
					# If there are no mob drops just throw these values instead just for fun (Putting them in CSUItems makes the counter show up on the UI)
					mission['m_iCSUItemID'][i] = taskInfo['startItems']['items'][i]
					mission['m_iCSUItemNumNeeded'][i] = taskInfo['startItems']['count'][i]

		if 'successItems' in taskInfo:
			for i in range(min(3, len(taskInfo['successItems']['items']))):
				mission['m_iSUItem'][i] = taskInfo['successItems']['items'][i]
				mission['m_iSUInstancename'][i] = taskInfo['successItems']['count'][i]

		if 'failItems' in taskInfo:
			for i in range(min(3, len(taskInfo['failItems']['items']))):
				mission['m_iFItemID'][i] = taskInfo['failItems']['items'][i]
				mission['m_iFItemNumNeeded'][i] = taskInfo['failItems']['count'][i]

		for i in range(min(2, len(MISSION_PREREQS))):
			mission['m_iCSTReqMission'][i] = MISSION_PREREQS[i]

		journalId = createJournalEntry(taskInfo['taskDesc'])
		mission['m_iSTJournalIDAdd'] = journalId
		mission['m_iSUJournalIDAdd'] = journalId # NOTE in some missions these are different? but it's a pretty useless thing
		
		# TODO implement task type 6 - escorts
		if taskInfo['taskType'] == 1 or taskInfo['taskType'] == 3 or taskInfo['taskType'] == 4: 
			mission['m_iHTerminatorNPCID'] = taskInfo['targetNPC']
			mission['m_iSTGrantWayPoint'] = taskInfo['targetNPC']
		elif taskInfo['taskType'] == 2:
			mission['m_iHTerminatorNPCID'] = taskInfo['target']
			mission['m_iSTGrantWayPoint'] = taskInfo['waypoint'] # Different in the case of entering fusion lairs; waypoint is for portal but actual target is inside the lair
		elif taskInfo['taskType'] == 5:
			if 'mobCount' in taskInfo: 
				for i in range(min(3, len(taskInfo['mobs']))):
					mission['m_iCSUEnemyID'][i] = taskInfo['mobs'][i]
					mission['m_iCSUNumToKill'][i] = taskInfo['mobCount'][i]
			else:
				mission['m_iCSUEnemyID'][0] = taskInfo['mobs'][0]
				for i in range(min(3, len(taskInfo['drops']))):
					mission['m_iCSUItemID'][i] = taskInfo['drops'][i]
					mission['m_iCSUItemNumNeeded'][i] = taskInfo['dropNum'][i]
					mission['m_iSTItemDropRate'][i] = taskInfo['dropRates'][i]
		elif taskInfo['taskType'] == 6:
			mission['m_iCSUDEFNPCAI'] = 6
			mission['m_iCSUDEFNPCID'] = taskInfo['escortNPC']

	for i in range(len(TASK_DATA)):
		taskInfo = TASK_DATA[i]

		mission = FFOrderedDict(0)
		addMissionData(mission, taskInfo)

		mission['m_iHTaskID'] = maxTaskId + i

		if 'timer' in taskInfo:
			mission['m_iSTGrantTimer'] = taskInfo['timer']
			mission['m_iCSUCheckTimer'] = taskInfo['timer']
			failMission = FFOrderedDict(0)
			addMissionData(failMission, taskInfo['failTask'])
			maxTaskId = maxTaskId + 1 # Failure task will be next, all tasks after are pushed down an index
			failMission['m_iHTaskID'] = maxTaskId + i
			mission['m_iFOutgoingTask'] = maxTaskId + i 
			failMission['m_iSUOutgoingTask'] = maxTaskId + i - 1 # Return to previous task, no +1 because maxTaskId was incremented
			missionData.append(failMission)

		if 'reqInstance' in taskInfo:
			mission['m_iRequireInstanceID'] = taskInfo['reqInstance']
			if mission['m_iFOutgoingTask'] != 0:
				mission['m_iFOutgoingTask'] = lastNonInstanceTask
		else:
			lastNonInstanceTask = maxTaskId + i
			

		if i == 0: 
			mission['m_iHNPCID'] = GIVER_ID

		if i == len(TASK_DATA) - 1:
			mission['m_iSUReward'] = reward['m_iMissionRewardID']
			for i in range(min(4, len(MISSION_COMPLETE_BARKERS))):
				mission['m_iHBarkerTextID'][i] = createMissionString(MISSION_COMPLETE_BARKERS[i])
		else:
			mission['m_iSUOutgoingTask'] = maxTaskId + i + 1

		missionData.append(mission)

	with open(TABLEDATA_PATH + '_new', 'wb') as f:
		tabledata.save(f)

main(tabledata)
