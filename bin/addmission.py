from unitypack.asset import Asset
from unitypack.object import FFOrderedDict

TABLEDATA_PATH = 'CustomAssetBundle-1dca92eecee4742d985b799d8226666d'
XDTINDEX = 7

# General mission data
MISSION_NAME = 'New frontier'
MISSION_TYPE = 3 # 1: guide 2: nano 3: world
MISSION_DIFFICULTY = 2 # 0: easy 1: normal 2: hard
REQUIRED_LEVEL = 1
GIVER_ID = 2555 # Future computress

MISSION_DESCRIPTION_TEXT = 'Hey, I hope this is working. I need you to go talk to someone to test this out.'
MISSION_COMPLETE_SUMMARY_TEXT = 'I helped test an experimental mission!'
NPC_MISSION_COMPLETE_SUMMARY_TEXT = 'I am pleased to see the results of this... let\'s try some more complex missions :)'
MISSION_SUMMARY_TEXT = 'Hell yeah this worked'

# Task data
# Task types - 1: talk to npc 2: touch waypoint 3: interact with object 4: deliver item to npc 5: kill mobs 6: escort
TASK_DATA = [
	{
		'journalNPC': 2555,
		'objective': 'Talk to Numbuh 8999 (and please don\'t crash lol)',
		'taskDesc': 'Let Numbuh 8999 know I got a custom mission in this bitch',
		'initialMessage': {
			'type': 2,
			'text': 'You are very brave for undertaking this task. Talk to Numbuh 8999 and inform them of our innovation.',
			'npc': 2555,
		},
		'initialDialog': {
			'text': 'Coke on her black skin made a stripe like a zebra, I call that jungle fever',
			'npc': 2555,
		},
		'successMessage': {
			'type': 2,
			'text': 'What a fucking genius you are.',
			'npc': 2969,
		},
		'successDialog': {
			'text': 'You will not control the threesome just roll the weed up until I get me some',
			'npc': 2969,
		},

		'taskType': 1,
		'targetNPC': 2969, # Future Numbuh 8999
	},
	{
		'journalNPC': 2555,
		'objective': 'Return to Computress.',
		'taskDesc': 'Come back to me :)',

		'taskType': 1,
		'targetNPC': 2555,
	}
]

# Reward data
REWARD_FM = 81836
REWARD_TAROS = 16384
# Items can also be added here

def main(tabledata):
	xdtdata = tabledata.objects[XDTINDEX].contents
	missionTable = xdtdata['m_pMissionTable']

	missionData = missionTable['m_pMissionData']
	missionStringData = missionTable['m_pMissionStringData']
	journalData = missionTable['m_pJournalData']
	rewardData = missionTable['m_pRewardData']

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
	for k,v in rewardData[0].items(): reward[k] = v

	reward['m_iMissionRewardID'] = len(rewardData)
	reward['m_iCash'] = REWARD_TAROS
	reward['m_iFusionMatter'] = REWARD_FM

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

	for i in range(len(TASK_DATA)):
		taskInfo = TASK_DATA[i]

		mission = FFOrderedDict(0)
		for k,v in missionData[0].items(): mission[k] = v

		mission['m_iHMissionID'] = missionId
		mission['m_iHTaskID'] = maxTaskId + i + 1
		mission['m_iHMissionName'] = nameId
		mission['m_iHJournalNPCID'] = taskInfo['journalNPC']

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

		journalId = createJournalEntry(taskInfo['taskDesc'])
		mission['m_iSTJournalIDAdd'] = journalId
		mission['m_iSUJournalIDAdd'] = journalId # NOTE in some missions these are different? but it's a pretty useless thing

		if i == 0: 
			mission['m_iHNPCID'] = GIVER_ID

		if i == len(TASK_DATA) - 1:
			mission['m_iSUReward'] = reward['m_iMissionRewardID']
		else:
			mission['m_iSUOutgoingTask'] = mission['m_iHTaskID'] + 1

		# TODO implement other task types
		if taskInfo['taskType'] == 1: 
			mission['m_iHTerminatorNPCID'] = taskInfo['targetNPC']
			mission['m_iSTGrantWayPoint'] = taskInfo['targetNPC']

		missionData.append(mission)

	with open(TABLEDATA_PATH + '_new', 'wb') as f:
		tabledata.save(f)
	
	
with open(TABLEDATA_PATH, 'rb') as f:
    tabledata = Asset.from_file(f)
    main(tabledata)