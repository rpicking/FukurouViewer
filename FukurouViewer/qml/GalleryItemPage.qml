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

        galleryItem = application.loadGallery(filepath, type)

        for(var key in galleryItem){
            var value = galleryItem[key]
            console.log(key, ": ", value)
        }        

        title.text = galleryItem.name
    }

    Item {
        id: topSection
        height: 280

        anchors {
            top: parent.top
            left: parent.left
            right: parent.right
        }

        // COVER
        Rectangle {
            color: "white"
            anchors.fill: coverImage
        }
        Image {
            id: coverImage
            x: 70
            Layout.preferredWidth: 200
            Layout.preferredHeight: 280
            fillMode: Image.PreserveAspectFit
            anchors.top: parent.top
        }

        ColumnLayout {
            spacing: 10

            anchors {
                left: coverImage.right
                top: parent.top
                right: parent.right
                bottom: parent.bottom
                margins: 5
            }

            // TITLE
            Text {
                id: title
                wrapMode: Text.WordWrap
                horizontalAlignment: Text.AlignHCenter
                font.pixelSize: 26

                Layout.leftMargin: 10
                Layout.rightMargin: 10
                Layout.fillWidth: true
            }

            Rectangle {
                height: 1
                Layout.fillWidth: true
                color: "#d3d3d3"
            }

            Item {
                Layout.fillHeight: true
                Layout.fillWidth: true

                Text {
                    id: tags
                    text: qsTr("Tags")
                    anchors {
                        left: parent.left
                        top: parent.top
                    }

                }
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
