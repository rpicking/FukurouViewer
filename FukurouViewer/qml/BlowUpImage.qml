import QtQuick 2.10


AnimatedImage {
    id: testImage
    property real scaleFactor: 1.0
    property int imageHeight: 0
    property int imageWidth: 0

    Component.onCompleted: {
        mainWindow.scrollBlowUp.connect(scaleImage);
    }

    function scaleImage(wheelScroll) {
        scaleFactor += 0.1 * wheelScroll;
        if (scaleFactor < 0) scaleFactor = 0;

        height = imageHeight * scaleFactor;
        width = imageWidth * scaleFactor;
    }

    onStatusChanged: {
        playing = (status === AnimatedImage.Ready);
        if (status === AnimatedImage.Ready) {
            imageHeight = height;
            imageWidth = width;
        }
    }
}
