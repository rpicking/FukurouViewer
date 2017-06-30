import QtQuick 2.0
import QtQuick.Window 2.2
import QtQuick.Controls 2.1

Component {
    //height: 80
    //width: 400

    Rectangle {
        id: root
        height: 80
        anchors.right: parent.right
        anchors.rightMargin: 15
        anchors.left: parent.left
        anchors.leftMargin: 0
        //border.width: 1

        function released() {
            console.log("HI THERE");
        }

        Text {
            id: nameField
            text: name
            anchors.top: parent.top
            anchors.topMargin: 10
            font.pointSize: 16
            anchors.left: parent.left
            anchors.leftMargin: 10
            elide: Text.ElideRight
        }

        Text {
            id: pathField
            text: path
            font.pointSize: 8
            font.italic: true
            anchors.top: nameField.bottom
            anchors.topMargin: 15
            anchors.left: nameField.left
            anchors.leftMargin: 20
        }

        Rectangle {
            id: colorBox
            width: height
            color: model.color
            border.width: 1
            anchors.top: parent.top
            anchors.topMargin: 10
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 10
            anchors.right: parent.right
            anchors.rightMargin: 5
        }

        Rectangle {
            height: 1
            color: theme.background
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.leftMargin: 15
            anchors.right: colorBox.right
            anchors.rightMargin: 5
        }

        MouseArea {
            propagateComposedEvents: true
            anchors.fill: parent
            onPressed: {
                console.log("HOLDING");
            }
            onReleased: {
                console.log("RELEASED");
            }
        }
    }
}
