import QtQuick 2.0
import QtQuick.Controls 2.5
import QtMultimedia 5.13

Item {
    property string filepath: ""
    property string type: ""

    Component.onCompleted: {
        loadSource();
        forceActiveFocus();
    }

    onActiveFocusChanged: {
        if (!activeFocus) return;

        itemLoader.forceActiveFocus();
    }

    function loadSource() {
        console.log(filepath + " | " + type);

        itemLoader.setSource("");

        var componentSource = "";
        switch (type) {
        case "IMAGE":
            componentSource = "ImageItemPage.qml";
            break;
        case "VIDEO":
            componentSource = "VideoItemPage.qml";
            break;
        case "ARCHIVE":
            componentSource = "GalleryItemPage.qml";
            break;
        default:
            console.log("No matching Page: " + type + " for file: " + filepath);
            return;
        }

        itemLoader.setSource(componentSource);
    }

    Loader {
        id: itemLoader
        asynchronous: true
        visible: itemLoader.status === Loader.Ready
        onStatusChanged: {
            if (itemLoader.status === Loader.Ready) {
                item.setFileSource(filepath, type);
             }
        }

        anchors.fill: parent
    }
}
