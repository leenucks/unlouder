import os
from sqlite3 import OperationalError
import string
import random
import threading
from flask import Response, redirect, render_template, request, Blueprint, stream_with_context, make_response
from werkzeug.utils import secure_filename
from telegram.Utils import DownloadFileHTTP, GenerateSHA256CheckSum, __Test, Test, Upload, uploadQueue, SearchCheckSum, statusToText
from telegram.config import files_dir
main = Blueprint('main', __name__)

@main.route('/home')
@main.route('/index')
@main.route('/')
def home():
	return render_template('home.html', title='Home')


@main.route('/download', methods=["GET"])
@main.route('/upload', methods=["GET"])
@main.route('/get', methods=["GET"])
@main.route('/cloud', methods=["GET"])
def cloud():
    #return render_template('cloud.html')
	return render_template('cloud.html', title='Cloud', urlUploadError=False, checksumDownloadError=False)


@main.route('/status/upload/<uploadStatusID>', methods=["GET"])
def _uploadStatus(uploadStatusID):
    try:
        with open(os.path.join(os.getcwd(), 'temp', f'_upload{uploadStatusID}.status'), 'r') as f:
            sts = f.read()

        if str(sts).split(":")[0] == 'True' or str(sts).split(":")[0] == 'Error':
            if os.path.exists(os.path.join(os.getcwd(), 'temp', f'_upload{uploadStatusID}.status')): os.remove(os.path.join(os.getcwd(), 'temp', f'_upload{uploadStatusID}.status'))
        return sts
    except FileNotFoundError: sts = 'Error:Error'; return sts


def _upload(uploadStatusID, uploadURL):
    statusToText(uploadStatusID, 'upload', 'False:Downloading file...')
    try:downloadedFile = DownloadFileHTTP(uploadURL, StatusID=uploadStatusID)
    except Exception as e: statusToText(uploadStatusID, 'upload', 'Error:Error Downloading... (was that direct download link?? Try again)'); return
    if (os.path.getsize(downloadedFile) / 1024 / 1024) >= 2000:
        statusToText(uploadStatusID, 'upload', 'Error:File larger than 2 Gigs, not yet supported...')
        try: os.remove(downloadedFile)
        except Exception as e: os.remove(f'{os.path.join(os.getcwd(), downloadedFile)}')
        return
    statusToText(uploadStatusID, 'upload', 'False:Getting checksum...')
    checksum = GenerateSHA256CheckSum(downloadedFile)
    statusToText(uploadStatusID, 'upload', 'False:Uploading file...')
    # uploadQueue.put((downloadedFile, checksum))
    # statusToText(uploadStatusID, 'upload', f'True:{checksum}')
    stst = Upload(downloadedFile, checksum, uploadStatusID)
    statusToText(uploadStatusID, 'upload', f'True:{checksum}')


@main.route('/upload', methods=["POST"])
def upload():
    uploadURL = request.form['uploadURL']
    uploadStatusID = ''.join((string.ascii_letters + string.digits)[random.randint(0, len((string.ascii_letters+string.digits))-1)] for x in range(16))
    threading.Thread(target=_upload, args=(uploadStatusID, uploadURL,)).start()
    
    _queue = uploadQueue.qsize()
    # print(_queue)
    return render_template('upload.html', title='TEST', uploadStatusID = uploadStatusID, checksum = '面白い !', queue = _queue)


@main.route('/download', methods=["POST"])
def download():
    downloadCheckSum = request.form.get('downloadCheckSum')
    print(downloadCheckSum)
    return redirect(f'/download/{downloadCheckSum}')
    # downloadStatusID = ''.join((string.ascii_letters + string.digits)[random.randint(0, len((string.ascii_letters+string.digits))-1)] for x in range(16))
    # threading.Thread(target=_download, args=(downloadStatusID, downloadCheckSum,)).start()
    # return render_template('download.html', title='TEST', downloadStatusID = downloadStatusID, checksum = '面白い !')
    

@main.route('/download/<downloadCheckSum>', methods=["GET"])
def downloadFile(downloadCheckSum):
    try:
        ID, NAME, SIZE = __Test(downloadCheckSum)
        print(ID, NAME)
        if ID and NAME:
            return Response(stream_with_context(Test(ID, NAME)), headers={
                            "Content-Type": "application/octet-stream",
                            "Content-Disposition": f'attachment; filename="{NAME}"',
                        },)
        else: return render_template('cloud.html', title='Cloud', urlUploadError=False, checksumDownloadError=True)
    except OperationalError or RuntimeError: return render_template('cloud.html', title='Cloud', urlUploadError=False, checksumDownloadError=True)




def _localUpload(uploadStatusID, save_path):
    pass
    '''
    if (os.path.getsize(save_path) / 1024 / 1024) >= 2000:
        statusToText(uploadStatusID, 'upload', 'Error:File larger than 2 Gigs, not yet supported...')
        try: os.remove(save_path)
        except Exception as e: os.remove(f'{os.path.join(os.getcwd(), save_path)}')
        return
    statusToText(uploadStatusID, 'upload', 'False:Getting checksum...')
    checksum = GenerateSHA256CheckSum(save_path)
    statusToText(uploadStatusID, 'upload', 'False:Uploading file...')
    stst = Upload(save_path, checksum, uploadStatusID)
    statusToText(uploadStatusID, 'upload', f'True:{checksum}')
    try: os.remove(save_path)
    except Exception as e: os.remove(f'{os.path.join(os.getcwd(), save_path)}')
    # return render_template('cloud.html', title='Cloud', urlUploadError=False, checksumDownloadError=True)
    '''




@main.route('/localUpload', methods=['POST'])
def localUpload():

    file = request.files['file']

    save_path = os.path.join(os.getcwd(), files_dir, secure_filename(file.filename))
    current_chunk = int(request.form['dzchunkindex'])

    # If the file already exists it's ok if we are appending to it,
    # but not if it's new file that would overwrite the existing one
    if os.path.exists(save_path) and current_chunk == 0:
        # 400 and 500s will tell dropzone that an error occurred and show an error
        return make_response(('File already exists', 400))

    try:
        with open(save_path, 'ab') as f:
            f.seek(int(request.form['dzchunkbyteoffset']))
            f.write(file.stream.read())
    except OSError:
        # log.exception will include the traceback so we can see what's wrong 
        print('Could not write to file')
        return make_response(("Not sure why,"
                            " but we couldn't write the file to disk", 500))

    total_chunks = int(request.form['dztotalchunkcount'])

    if current_chunk + 1 == total_chunks:
        # This was the last chunk, the file should be complete and the size should be matched
        if os.path.getsize(save_path) != int(request.form['dztotalfilesize']):
            print(f"File {file.filename} was completed, "
                    f"but has a size mismatch."
                    f"Was {os.path.getsize(save_path)} but we"
                    f" expected {request.form['dztotalfilesize']} ")
            return make_response(('Size mismatch', 500))
        else:
            print(f'File {file.filename} has been uploaded successfully')
            uploadStatusID = ''.join((string.ascii_letters + string.digits)[random.randint(0, len((string.ascii_letters+string.digits))-1)] for x in range(16))
            #threading.Thread(target=_localUpload, args=(uploadStatusID, save_path,)).start()
            checksum = GenerateSHA256CheckSum(save_path)
            uploadQueue.put((save_path, checksum))
            print(checksum)
            return make_response((checksum, 200))

            # checksum = GenerateSHA256CheckSum(save_path)
            # stst = Upload(save_path, checksum)
            # print("Done")
            # try: os.remove(save_path)
            # except Exception as e: os.remove(f'{os.path.join(os.getcwd(), save_path)}')

    else:
        print(f'Chunk {current_chunk + 1} of {total_chunks} '
                f'for file {file.filename} complete')


    return make_response(("Chunk upload successful", 200))
    # return redirect('/home')
