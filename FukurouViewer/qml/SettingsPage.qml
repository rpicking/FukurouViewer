import QtQuick 2.0
import QtQuick.Controls 2.3

Item {
    id: element1
    property string tab: "default"
    width: 1000
    height: 1000

    Component.onCompleted: {
        console.log(tab);
        //topBar.state = "settings";
    }

    Text {
        text: "Settings"
        fontSizeMode: Text.Fit
        minimumPixelSize: 12
        width: parent.width
        height: parent.height
        font.pointSize: 800
        verticalAlignment: Text.AlignVCenter
    }

    ScrollView {
        id: settingsScroll
        anchors.fill: parent

        Column {
            id: column
            height: 400
            anchors.right: parent.right
            anchors.left: parent.left
            anchors.top: parent.top

            Rectangle {
                id: thumbnailSection
                height: 200
                color: "#ffffff"
                anchors.right: parent.right
                anchors.rightMargin: 0
                anchors.left: parent.left
                anchors.leftMargin: 0

                Text {
                    id: sectionTitle
                    x: 10
                    y: 10
                    text: qsTr("Thumbnails")
                    font.underline: false
                    anchors.top: parent.top
                    anchors.topMargin: 10
                    anchors.left: parent.left
                    anchors.leftMargin: 10
                    font.pixelSize: 30
                }

                Text {
                    id: sectionTitle1
                    x: 2
                    y: 2
                    text: qsTr("Thumbnails")
                    anchors.leftMargin: 10
                    anchors.top: parent.top
                    font.pixelSize: 30
                    anchors.left: parent.left
                    font.underline: false
                    anchors.topMargin: 10
                }
            }

            Rectangle {
                id: downloadsSection
                height: 200
                color: "#ffffff"
                anchors.right: parent.right
                anchors.leftMargin: 0
                anchors.left: parent.left
                anchors.rightMargin: 0
            }
        }
    }
}

/*##^## Designer {
    D{i:5;anchors_x:227;anchors_y:226}D{i:6;anchors_x:227;anchors_y:226}D{i:4;anchors_width:200}
D{i:7;anchors_width:200}D{i:3;anchors_height:400;anchors_width:200}D{i:2;anchors_height:200;anchors_width:200}
}
 ##^##*/
