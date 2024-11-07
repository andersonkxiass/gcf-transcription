def convert(event, context):
    """Triggered by a change to a Cloud Storage bucket.
    Args:
         event (dict): Event payload.
         context (google.cloud.functions.Context): Metadata for the event.
    """
    from google.cloud import storage
    import ffmpeg

    storage_client = storage.Client()

    file = event

    gcs_file_name = file['name']
    file_name, type_extension = gcs_file_name.split(".")

    bucket_video = storage_client.bucket("audionote-transcribe-video")
    bucket_audio = storage_client.bucket("audionote-transcribe-audio")

    blob = bucket_video.get_blob(blob_name=f"{gcs_file_name}")
    blob.download_to_filename(f'/tmp/temp_{gcs_file_name}')

    try:

        ffmpeg.input(f'/tmp/temp_{gcs_file_name}', ss=1) \
            .output('/tmp/temp.wav', format='wav') \
            .overwrite_output() \
            .run(capture_stdout=True, capture_stderr=True)

    except ffmpeg.Error as e:
        print(e.stderr.decode())
        exit(0)

    blob_audio = bucket_audio.blob(f"{file_name}.wav")
    blob_audio.upload_from_filename(f'/tmp/temp.wav', content_type="audio/wav")
