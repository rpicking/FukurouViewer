import QtQuick 2.0


Component {
    id: historyDelegateItem
    Rectangle {
        height: 50
        anchors.right: parent.right
        anchors.rightMargin: 15
        anchors.left: parent.left
        anchors.leftMargin: 0
        //border.width: 1

        Text {
            text: filename
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.right: thumbnail.left
            anchors.rightMargin: 0
            elide: Text.ElideRight
            anchors.verticalCenter: parent.verticalCenter
        }

        Image {
            anchors.top: parent.top
            anchors.topMargin: 5
            anchors.right: parent.right
            anchors.rightMargin: 0
            id: thumbnail
            //anchors.fill: parent
            //fillMode: Image.Stretch
            sourceSize.width: parent.height - 10
            sourceSize.height: parent.height - 10
            source: "image://fukurou/" + id
        }
        Rectangle {
            height: 1
            color: theme.background
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.leftMargin: 15
            anchors.right: thumbnail.right
            anchors.rightMargin: 5
        }
    }
}
