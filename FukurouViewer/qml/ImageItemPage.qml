import QtQuick 2.0
import QtQuick.Controls 2.5
import QtMultimedia 5.13

Item {

    anchors.fill: parent

    function setFileSource(imageSource, type) {
        image.source = "file:///" + imageSource;
    }

    AnimatedImage {
        id: image
        fillMode: Image.PreserveAspectFit
        smooth: true
        anchors.fill: parent
    }
}
