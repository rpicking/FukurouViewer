import QtQuick 2.0
import QtGraphicalEffects 1.0
import QtQuick.Controls 2.1
//import QtQml 2.2

//Item {
Component {
    id: root
    Rectangle {
        id: rectangle
        height: 50
        anchors.right: parent.right
        anchors.rightMargin: 6
        anchors.left: parent.left
        anchors.leftMargin: 0
        //border.width: 1

        Text {
            text: filename
            font.strikeout: model.dead
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.right: thumbnail.left
            anchors.rightMargin: 0
            elide: Text.ElideRight
            anchors.verticalCenter: parent.verticalCenter
        }

        Image {
            id: thumbnail
            height: parent.height - 20
            width: parent.height - 20
            anchors.verticalCenter: parent.verticalCenter
            anchors.right: closeButton.left
            anchors.rightMargin: 0
            //anchors.fill: parent
            //fillMode: Image.Stretch
            sourceSize.width: height
            sourceSize.height: width
            source: "image://fukurou/" + id
        }

        Colorize {
            visible: model.dead
            anchors.fill: thumbnail
            source: thumbnail
            hue: 0.0
            saturation: 0.0
            lightness: 0.0
        }

        TextIconButton {
            id: closeButton
            fontFamily: fontAwesome.name
            buttonText: "\uf00d"
            textField.font.pointSize: 16
            textField.color: mouseArea.containsMouse ? "#919191" : "#cecece"
            ToolTip.visible: mouseArea.containsMouse
            ToolTip.text: qsTr("Remove item from list")
            ToolTip.delay: 1000
            anchors.right: parent.right
            anchors.rightMargin: 0
            anchors.verticalCenter: parent.verticalCenter
            verticalOffset: -1

            mouseArea.onClicked: {
                console.log(model.id);
                mainWindow.deleteHistoryItem(model.id);
            }
        }

        Rectangle {
            anchors {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            height: 1
            color: "lightgrey"
        }

    }
}
