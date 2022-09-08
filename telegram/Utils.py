import os, time, queue
import random
import string
from hashlib import sha256
import shutil
from sqlite3 import OperationalError
from pySmartDL import SmartDL
from pyrogram import Client
import asyncio
import threading
from .config import api_id, api_hash, bot_token, channel_id, files_dir, download_dir

import nest_asyncio
nest_asyncio.apply()

uploadQueue = queue.Queue()

loop = asyncio.get_event_loop()

app = Client("my_account", workdir = os.path.join(os.getcwd(), 'sessions'), api_id=api_id, api_hash=api_hash)
app1 = Client("my_bot", workdir = os.path.join(os.getcwd(), 'sessions'), api_id=api_id, api_hash=api_hash, bot_token=bot_token)

def CopyClient():
	newSession = ''.join((string.ascii_letters + string.digits)[random.randint(0, len((string.ascii_letters+string.digits))-1)] for x in range(6))
	shutil.copy(os.path.join(os.getcwd(), 'sessions', "my_account.session"), os.path.join(os.getcwd(), 'sessions', f"{newSession}.session"))
	return newSession

def RemoveClient(sessionToDelete):
	os.remove(os.path.join(os.getcwd(), 'sessions', f'{sessionToDelete}.session'))

def statusToText(StatusID, statusType, text):
    if not os.path.isdir(os.path.join(os.getcwd(), 'temp')):
        os.mkdir(os.path.join(os.getcwd(), 'temp'))
        
    if str(statusType).lower()[0] == 'u':
        
        with open(os.path.join(os.getcwd(), 'temp', f'_upload{StatusID}.status'), 'w') as f:
            f.write(text)
            f.close()
    elif str(statusType).lower()[0] == 'd': #### DEPRECIATED #### Now, it directly Streams File

        with open(os.path.join(os.getcwd(), 'temp', f'_download{StatusID}.status'), 'w') as f:
            f.write(text)
            f.close()

def DownloadFileHTTP(URL, download_dir=download_dir, StatusID = None):

	FileDownloader = SmartDL(URL, download_dir)
	FileDownloader.start(blocking=False)


	while not FileDownloader.isFinished():
		text = f'False:Downloading... ({round(FileDownloader.get_progress(), 2) * 100} %)'
		statusToText(StatusID, 'upload', text)
		time.sleep(1)

	if FileDownloader.isSuccessful():
		FileToUpload = FileDownloader.get_dest()
		return FileToUpload
	else: return statusToText(StatusID, 'upload', 'Error:Error Downloading... (Try again, maybe ??)')	
	# never reaches below lol
	FileToUpload = FileDownloader.get_dest()
	return FileToUpload


def GenerateSHA256CheckSum(file):

	sha256sum = sha256()
	with open( file, 'rb' ) as f:
		data_chunk = f.read(1024)
		while data_chunk:
			sha256sum.update(data_chunk)
			data_chunk = f.read(1024)
		checksum = sha256sum.hexdigest()
	return(checksum)


async def upload(file, captionCheckSum, uploadStatusID):
	# Keep track of the progress while uploading
	async def progress(current, total):
		percentComplete = f"{current * 100 / total:.1f} %"
		text = f'False:Uploading... ({percentComplete})'
		statusToText(uploadStatusID, 'upload', text)

	newSession = CopyClient()
	async with Client(newSession, workdir = os.path.join(os.getcwd(), 'sessions')) as app0:
		await app0.send_document(channel_id, file, caption = captionCheckSum, progress = progress)
	RemoveClient(newSession)
	return True

def Upload(file, captionCheckSum, uploadStatusID):
	return loop.run_until_complete(upload(file, captionCheckSum, uploadStatusID))



######################### LOCAL UPLOAD ##############################

async def _upload(_task):
	# Keep track of the progress while uploading uploadQueue file, captionCheckSum, uploadStatusID
	#while True:
		#_task = uploadQueue.get()
	save_path, checksum = _task
	print(save_path, checksum)

	async def progress(current, total):
		percentComplete = f"{current * 100 / total:.1f} %"
		text = f'False:Uploading... ({percentComplete})'
		print(text, end='\r')

	newSession = CopyClient()
	async with Client(newSession, workdir = os.path.join(os.getcwd(), 'sessions')) as app0:
		await app0.send_document(channel_id,save_path, caption = checksum, progress = progress)
	RemoveClient(newSession)
	try: os.remove(save_path)
	except Exception as e: os.remove(os.path.join(os.getcwd(), 'files', save_path))


def _Upload(_task):
	loop.run_until_complete(_upload(_task))

def lol():
	while True:
		_task = uploadQueue.get()
		_Upload(_task)

t = threading.Thread(target=lol).start()
# _Upload(uploadQueue)



# async def download(FileNameList, FileIdList, FileSizeList):
# 	DownloadedFileNameList = []
# 	indexFileName = 0
# 	async def progress(current, total):
# 		total = FileSize
# 		try:
# 			percentComplete = f"{round(((current * 100 ) / total), 2)} %"
# 			print(percentComplete, end='\r')

# 		except ZeroDivisionError: pass
	
# 	async with app1:
# 		for FileId in FileIdList:
# 			FileName = FileNameList[indexFileName]
# 			FileSize = FileSizeList[indexFileName]
# 			print(f'{FileId}')
# 			DownloadDir = os.path.join(os.getcwd(), FileName)
# 			await app1.download_media(FileId, file_name=DownloadDir, progress=progress)
# 			indexFileName += 1
# 			DownloadedFileNameList.append(FileName)
# 	return DownloadedFileNameList

# def Download(FileNameList, FileIdList, FileSizeList):
# 	return loop.run_until_complete(download(FileNameList, FileIdList, FileSizeList))

async def searchCheckSum(checksum):
	FileName = []
	FileId = []
	FileSize = []
	newSession = CopyClient()
	async with Client(newSession, workdir = os.path.join(os.getcwd(), 'sessions')) as app0:
		async for message in app0.search_messages(channel_id, checksum):
			try:
				print(message)
				FileName.append(message.document.file_name)
				FileId.append(message.document.file_id)
				FileSize.append(message.document.file_size)
				status = True
				searchReturnType = 'document'
				payload = {

					'fileNameList' : FileName,
					'fileIdList' : FileId,
					'fileSizeList' : FileSize

				}
				
			except AttributeError: 
				print("It's a message not document")
				status = True
				searchReturnType = 'message'
				payload = f'{message.id}:{message.text}'
	RemoveClient(newSession)	
	try: return status, searchReturnType, payload
	except UnboundLocalError: status, searchReturnType, payload = False, 'empty', None; return status, searchReturnType, payload


def SearchCheckSum(checksum):
	return loop.run_until_complete(searchCheckSum(checksum))





async def test(ID, NAME):
	newSession = CopyClient()
	try:
		async with Client(newSession, workdir=os.path.join(os.getcwd(), 'sessions')) as app0:
			async for chunk in app0.stream_media(ID):
				yield (chunk)
		RemoveClient(newSession)
	except Exception as e: RemoveClient(newSession); Test(ID, NAME)

def _Test(test):
	# lp = asyncio.new_event_loop()

	test = test.__aiter__()
	async def get_next():
		try:
			obj = await test.__anext__()
			return False, obj
		except StopAsyncIteration:
			return True, None
	while True:
		done, obj = loop.run_until_complete(get_next())
		if done: break
		yield obj


def __Test(downloadCheckSum):
	searchStatusFileFound, searchReturnMessageType, searchReturnPayload = SearchCheckSum(downloadCheckSum)
	if searchStatusFileFound and searchReturnMessageType.lower() == 'document':
		ID = searchReturnPayload['fileIdList'][0]
		NAME = searchReturnPayload['fileNameList'][0]
		SIZE = searchReturnPayload['fileSizeList'][0]
		return (ID, NAME, SIZE)
	else: return(None, None, None)

def Test(ID, NAME):
	print(ID, NAME)
	ait = test(ID, NAME)
	yield from _Test(ait)