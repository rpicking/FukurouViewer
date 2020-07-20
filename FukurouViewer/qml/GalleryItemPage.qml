import QtQuick 2.0
import QtQuick.Layouts 1.12

Item {
    property string filepath: ""
    property var galleryItem: undefined

    anchors.fill: parent

    function setFileSource(gallerySource, type) {
        filepath = gallerySource;

        console.log(type);

        coverImage.source = "image://thumbs/" + encodeURIComponent(filepath);
        title.text = gallerySource;

        galleryItem = application.loadGallery(filepath, type)
        for(var key in galleryItem){
            var value = galleryItem[key]
            console.log(key, ": ", value)
        }
    }

    Rectangle {
        id: topSection
        height: 280

        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
        }

        // COVER
        Rectangle {
            color: "#000000"
            anchors.fill: coverImage
        }
        Image {
            id: coverImage
            x: 70
            Layout.preferredWidth: 200
            Layout.preferredHeight: 280
            fillMode: Image.PreserveAspectFit
            anchors.top: parent.top
            anchors.topMargin: 0
        }

        // TITLE
        Text {
            id: title
            height: 150
            text: qsTr("Text")            

            font.pixelSize: 16

            anchors {
                left :parent.left
                leftMargin: 610
                top: parent.top
                right: topSection.right
            }
        }
    }

    // GRID VIEW of files
    // if archive, loaded from memory
    GalleryView {
        id: test
        usedModel: galleryGridModel

        anchors {
            top: topSection.bottom
            topMargin: 10
            bottom: parent.bottom
            left: parent.left
            right: parent.right
        }
    }

}

/*##^##
Designer {
    D{i:0;autoSize:true;formeditorZoom:0.5;height:970;width:1500}
}
##^##*/
