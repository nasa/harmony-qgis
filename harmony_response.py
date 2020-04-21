def handleHarmonyResponse(iface, response, layerName, variable):
    with open('/tmp/harmony_output_image.tif', 'wb') as fd:
        for chunk in response.iter_content(chunk_size=128):
            fd.write(chunk)

    iface.addRasterLayer('/tmp/harmony_output_image.tif', layerName + '-' + variable)
    