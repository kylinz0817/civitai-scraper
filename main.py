import json
import logging
import time
from datetime import datetime
from os import mkdir
from os.path import isdir

import cloudscraper
import requests
from bs4 import BeautifulSoup

logging.basicConfig(
	format="{asctime} - {levelname} - {message}",
	datefmt="%Y-%m-%d %H:%M",
	level=logging.DEBUG,
	style="{"
)

# modelVersions.id	modelVersions.name	modelVersions.description	modelVersions.createdAt	modelVersions.downloadUrl
# modelVersions.trainedWords	modelVersions.files.sizeKb

# gencost.quantity	gencost.size	gencost.base
# gencost.addresource	gencost.creatortip	gencost.civitaitip

# remix.workflow	remix.model	num_remix.addresources
# remix_addresourcestype	remix_prompt	remix_triggerwords	remix_negprompt

# stats.downloadCount	stats.favoriteCount	stats.commentCount	stats.ratingCount	stats.rating
# modelEarlyaccess	earlyaccess.donation	earlyaccess.timeframe
# gencost.popularity	gencost.sampler


api = 'https://civitai.com/api'
limit = 10
cut_off_date = datetime(2025, 3, 25)


def processModel(model):
	logging.info(f'Processing model {model["id"]}')
	with open(f"./model_api/{model['id']}.json", 'w', encoding='utf-8') as f:
		json.dump(model, f, ensure_ascii=False, indent=4)
	# logging.debug(json.dumps(model, indent=4))
	# id	name	description	type	nsfw	tags	mode	creator.username	creator.image
	data = {
		"model.id": model['id'],
		"model.name": model['name'],
		"model.description": model['description'],
		"model.type": model['type'],
		"model.nsfw": model['nsfw'],
		"model.nsfwLevel": model['nsfwLevel'],
		"model.tags": ", ".join(model['tags']),
		"model.mode": model.get('mode', None),
		"model.creator.username": model['creator']['username'],
		"model.creator.image": model['creator']['image'],
		"model.stats.downloadCount": model['stats']['downloadCount'],
		"model.stats.favoriteCount": model['stats']['favoriteCount'],
		"model.stats.commentCount": model['stats']['commentCount'],
		"model.stats.ratingCount": model['stats']['ratingCount'],
		"model.stats.rating": model['stats']['rating'],
		"model.stats.thumbsUpCount": model['stats']['thumbsUpCount'],
		"model.stats.thumbsDownCount": model['stats']['thumbsDownCount'],
		"model.stats.tippedAmountCount": model['stats']['tippedAmountCount'],

		"model.availability": model['availability'],
		"model.allowNoCredit": model['allowNoCredit'],
		"model.allowCommercialUse": ", ".join(model['allowCommercialUse']) if "allowCommercialUse" in model else None,
		"model.allowDerivatives": model['allowDerivatives'],
		"model.allowDifferentLicense": model['allowDifferentLicense'],
		"model.minor": model['minor'],
		"model.poi": model['poi'],
		"model.cosmetic": model['cosmetic'],
		"model.supportsGeneration": model['supportsGeneration'],
	}
	versions = []
	modelData = getModelData(model['id'])
	for modelversion in model['modelVersions']:
		file = modelversion['files'][0]
		version = {
			"modelVersion.id": modelversion['id'],
			"modelVersion.name": modelversion['name'],
			"modelVersion.description": modelversion.get('description', None),
			"modelVersion.createdAt": modelversion['createdAt'],
			"modelVersion.downloadUrl": modelversion['downloadUrl'],
			"modelVersion.trainedWords": ", ".join(
				modelversion['trainedWords']) if "trainedWords" in modelversion else None,
			"modelVersion.files.sizeKb": file['sizeKB'],

			"modelVersion.versionBaseModel": modelversion['baseModel'],
			"modelVersion.versionBaseModelType": modelversion[
				'baseModelType'] if "baseModelType" in modelversion else None,
			"modelVersion.versionStatus": modelversion['status'],
			"modelVersion.versionAvailability": modelversion['availability'],
			"modelVersion.versionNsfwLevel": modelversion['nsfwLevel'],
			"modelVersion.versionFileName": file['name'],
			"modelVersion.versionFileType": file['type'],
		}
		version_data = getModelVersion(model['id'], modelversion['id'])
		version.update(version_data)
		if modelversion['id'] in modelData:
			version.update(modelData[modelversion['id']])
		versions.append(version)
	data['modelVersions'] = versions
	logging.info(json.dumps(data, indent=4))
	with open(f"./result/{model['id']}.json", 'w', encoding='utf-8') as f:
		json.dump(data, f, ensure_ascii=False, indent=4)


def getModelData(model_id):
	logging.info(f'Getting model data for {model_id}')
	url = f'https://civitai.com/models/{model_id}'
	res = cloudscraper.create_scraper().get(url)
	soup = BeautifulSoup(res.content, 'lxml')
	script = json.loads(soup.find("script", {"id": "__NEXT_DATA__"}).text)
	with open(f"./model/{model_id}.json", 'w', encoding='utf-8') as f:
		json.dump(script, f, ensure_ascii=False, indent=4)
	versionData = {}
	queries = script['props']['pageProps']['trpcState']['json']['queries']
	for query in queries:
		if "getById" not in query['queryHash']:
			continue
		state = query['state']['data']
		if state['id'] != model_id:
			continue
		rank = state['rank']
		for modelVersion in state['modelVersions']:
			if modelVersion['earlyAccessDeadline']:
				donationGoal = getDonationGoal(modelVersion['id'])
			else:
				donationGoal = {"goalAmount": None, "total": None}
			data = {
				"modelVersion.GenerationCountAllTime": modelVersion['rank']['generationCountAllTime'],
				"modelVersion.DownloadCountAllTime": modelVersion['rank']['downloadCountAllTime'],
				"modelVersion.RatingCountAllTime": modelVersion['rank']['ratingCountAllTime'],
				"modelVersion.RatingAllTime": modelVersion['rank']['ratingAllTime'],
				"modelVersion.ThumbsUpCountAllTime": modelVersion['rank']['thumbsUpCountAllTime'],
				"modelVersion.ThumbsDownCountAllTime": modelVersion['rank']['thumbsDownCountAllTime'],
				"modelVersion.name": modelVersion['name'],
				"modelVersion.id": modelVersion['id'],
				"modelVersion.modelId": modelVersion['modelId'],
				"model.downloadCountAllTime": rank['downloadCountAllTime'],
				"model.favoriteCountAllTime": rank['favoriteCountAllTime'],
				"model.thumbsUpCountAllTime": rank['thumbsUpCountAllTime'],
				"model.thumbsDownCountAllTime": rank['thumbsDownCountAllTime'],
				"model.commentCountAllTime": rank['commentCountAllTime'],
				"model.ratingCountAllTime": rank['ratingCountAllTime'],
				"model.ratingAllTime": rank['ratingAllTime'],
				"model.tippedAmountCountAllTime": rank['tippedAmountCountAllTime'],
				"model.imageCountAllTime": rank['imageCountAllTime'],
				"model.collectedCountAllTime": rank['collectedCountAllTime'],
				"model.generationCountAllTime": rank['generationCountAllTime'],
				"model.earlyAccessDeadlineModel": state['earlyAccessDeadline'],
				"modelVersion.earlyAccessEndsAt": modelVersion['earlyAccessEndsAt'],

				"modelVersion.earlyAccessDeadline": modelVersion['earlyAccessDeadline'],
				"modelVersion.donationGoalAmount": donationGoal['goalAmount'],
				"modelVersion.donationGoalTotal": donationGoal['total'],
			}
			if modelVersion['earlyAccessConfig']:
				data["modelVersion.earlyAccessConfig.timeframe"] = modelVersion['earlyAccessConfig']['timeframe']
				data["modelVersion.earlyAccessConfig.donationGoal"] = modelVersion['earlyAccessConfig'][
					'donationGoal'] if "donationGoal" in modelVersion['earlyAccessConfig'] else None
				data["modelVersion.earlyAccessConfig.downloadPrice"] = modelVersion['earlyAccessConfig'][
					'downloadPrice']
				data["modelVersion.earlyAccessConfig.donationGoalId"] = modelVersion['earlyAccessConfig'][
					'donationGoalId'] if "donationGoalId" in modelVersion['earlyAccessConfig'] else None
				data["modelVersion.earlyAccessConfig.generationPrice"] = modelVersion['earlyAccessConfig'][
					'generationPrice']
				data["modelVersion.earlyAccessConfig.chargeForDownload"] = modelVersion['earlyAccessConfig'][
					'chargeForDownload']
				data["modelVersion.earlyAccessConfig.originalTimeframe"] = modelVersion['earlyAccessConfig'][
					'originalTimeframe']
				data["modelVersion.earlyAccessConfig.chargeForGeneration"] = modelVersion['earlyAccessConfig'][
					'chargeForGeneration']
				data["modelVersion.earlyAccessConfig.donationGoalEnabled"] = modelVersion['earlyAccessConfig'][
					'donationGoalEnabled']
				data["modelVersion.earlyAccessConfig.originalPublishedAt"] = modelVersion['earlyAccessConfig'][
					'originalPublishedAt']
				data["modelVersion.earlyAccessConfig.generationTrialLimit"] = modelVersion['earlyAccessConfig'][
					'generationTrialLimit']
			versionData[modelVersion['id']] = data
	return versionData


def getDonationGoal(modelVersionId):
	logging.info(f'Getting donation goal for model version {modelVersionId}')
	url = f'https://civitai.com/api/trpc/modelVersion.donationGoals?input={{"json":{{"id":{modelVersionId},"authed":true}}}}'
	res = getRes(url).json()
	data = res['result']['data']['json'][0]
	return {"goalAmount": data['goalAmount'], "total": data['total']}


def getModel(model_id):
	logging.info(f'Getting model {model_id}')
	url = f'{api}/v1/models/{model_id}'
	res = getRes(url).json()
	processModel(res)


def getModelVersion(model_id, version_id):
	logging.info(f'Getting model {model_id} version {version_id}')
	url = f'{api}/v1/model-versions/{version_id}'
	res = getRes(url).json()
	with open(f'./model-version/{model_id}_{version_id}.json', 'w', encoding='utf-8') as f:
		json.dump(res, f, ensure_ascii=False, indent=4)
	# logging.debug(json.dumps(res, indent=4))
	stats = res['stats']
	data = {
		"modelVersion.id": res['id'],
		"modelVersion.name": res['name'],
		"modelVersion.createdAt": res['createdAt'],
		"modelVersion.updatedAt": res['updatedAt'],
		"modelVersion.status": res['status'],
		"modelVersion.publishedAt": res['publishedAt'],
		"modelVersion.trainedWords": ", ".join(res['trainedWords']),
		"modelVersion.trainingStatus": res['trainingStatus'],
		"modelVersion.trainingDetails": res['trainingDetails'],
		"modelVersion.baseModel": res['baseModel'],
		"modelVersion.baseModelType": res['baseModelType'],
		"modelVersion.earlyAccessEndsAt": res['earlyAccessEndsAt'],
		"modelVersion.description": res['description'],
		"modelVersion.stats.downloadCount": stats['downloadCount'],
		"modelVersion.stats.ratingCount": stats['ratingCount'],
		"modelVersion.stats.rating": stats['rating'],
		"modelVersion.stats.thumbsUpCount": stats['thumbsUpCount'],
		"model.name": res['model']['name'],
		"model.type": res['model']['type'],
		"images": []
	}
	for image in res['images']:
		image_data = {
			"image.url": image['url'],
			"image.nsfwLevel": image['nsfwLevel'],
			"image.type": image['type'],
			"image.metadata.size": image['metadata']['size'],
			"image.prompt": image['meta']['prompt'],
			"image.sampler": image['meta']['sampler'],
			"image.steps": image['meta']['steps'],
			"image.cfgScale": image['meta']['cfgScale'],
			"image.negativePrompt": image['meta']['negativePrompt'] if "negativePrompt" in image['meta'] else None,
		}
		data["images"].append(image_data)
	# logging.debug(json.dumps(data, indent=4))
	return data


def getAllModels():
	logging.info('Getting all models')
	url = f'{api}/v1/models?sort=Newest&limit={limit}'
	should_continue = True
	while should_continue:
		res = getRes(url).json()
		for model in res['items']:
			processModel(model)
			if len(model['modelVersions']) > 0:
				first_model_version = model['modelVersions'][0]
				if datetime.strptime(first_model_version['publishedAt'], '%Y-%m-%dT%H:%M:%S.%fZ') < cut_off_date:
					should_continue = False
					break
		url = res['metadata']['nextPage']
		if url is None:
			should_continue = False


def main():
	logo()
	for x in ['model_api', 'model-version', 'image', 'result', 'model']:
		if not isdir(x):
			mkdir(x)
	# getAllModels()
	getModel('297100')


def logo():
	print(r"""
    _________  .__        .__   __      _____   .___ 
    \_   ___ \ |__|___  __|__|_/  |_   /  _  \  |   |
    /    \  \/ |  |\  \/ /|  |\   __\ /  /_\  \ |   |
    \     \____|  | \   / |  | |  |  /    |    \|   |
     \______  /|__|  \_/  |__| |__|  \____|__  /|___|
            \/                               \/      
==========================================================
      API based CivitAI Scraper by Muhammad Hassan 
          (https://github.com/evilgenius786)
==========================================================
[+] API Based
[+] Scrapes tips and donation info
[+] Scrapes stats like remix and downloads count
[+] Scrapes early access information
[+] Scrapes resource information
[+] Scrapes model versions
__________________________________________________________
""")
	time.sleep(0.1)


def getRes(url, params=None):
	logging.info(f'Getting response from {url}')
	return requests.get(url, params=params)


if __name__ == '__main__':
	main()

# def getImageData(img_id):
#     url = f"https://civitai.com/api/generation/data?type=image&id={img_id}"
#     res = getRes(url).json()
#     params = res['params']
#     data = {
#         "prompt":  params['prompt'],
#         'negativePrompt': params['negativePrompt'],
#         'sampler': params['sampler'],
#     }
#     return data
# def getModelVersion(model_version):
#     url = f"https://civitai.com/api/generation/data?type=modelVersion&id={model_version}"
#     res = getRes(url).json()

# https://civitai.com/api/trpc/modelVersion.donationGoals?input=%7B%22json%22%3A%7B%22id%22%3A1546235%2C%22authed%22%3Atrue%7D%7D
# https://civitai.com/api/trpc/orchestrator.getImageWhatIf?input=%7B%22json%22%3A%7B%22resources%22%3A%5B%7B%22id%22%3A128713%7D%2C%7B%22id%22%3A333803%2C%22epochNumber%22%3Anull%7D%5D%2C%22params%22%3A%7B%22workflow%22%3A%22txt2img%22%2C%22cfgScale%22%3A3.5%2C%22steps%22%3A25%2C%22sampler%22%3A%22DPM%2B%2B%202M%20Karras%22%2C%22seed%22%3Anull%2C%22clipSkip%22%3A2%2C%22quantity%22%3A2%2C%22aspectRatio%22%3A%220%22%2C%22prompt%22%3A%22%22%2C%22negativePrompt%22%3Anull%2C%22nsfw%22%3Afalse%2C%22baseModel%22%3A%22SD1%22%2C%22denoise%22%3A0.4%2C%22upscale%22%3A1.5%2C%22civitaiTip%22%3A0%2C%22creatorTip%22%3A0.25%2C%22fluxUltraAspectRatio%22%3A%224%22%2C%22fluxMode%22%3A%22urn%3Aair%3Aflux1%3Acheckpoint%3Acivitai%3A618692%40691639%22%2C%22priority%22%3A%22low%22%2C%22sourceImage%22%3Anull%2C%22experimental%22%3Afalse%2C%22width%22%3A512%2C%22height%22%3A512%2C%22remixSimilarity%22%3A1%7D%2C%22authed%22%3Atrue%7D%2C%22meta%22%3A%7B%22values%22%3A%7B%22resources.1.epochNumber%22%3A%5B%22undefined%22%5D%2C%22params.seed%22%3A%5B%22undefined%22%5D%2C%22params.negativePrompt%22%3A%5B%22undefined%22%5D%7D%7D%7D
# https://civitai.com/api/v1/models/1391178
# https://civitai.com/api/v1/models?sort=Newest&limit=1
