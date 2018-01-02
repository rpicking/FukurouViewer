import QtQuick 2.0
import QtQuick.Controls 2.1
import QtGraphicalEffects 1.0

//Item {
Component {
    //width: 400
    //height: 100
    Rectangle {
        id: root
        height: 100
        anchors.right: parent.right
        anchors.left: parent.left

        Text {
            id: filename
            width: 250
            height: 20
            text: model.filename
            font.pointSize: 12
            elide: Text.ElideRight
            anchors {
                top: parent.top
                topMargin: 10
                left: parent.left
                leftMargin: 10
            }
        }

        Text {
            id: speed
            text: model.speed + "/s"
            font.pointSize: 10
            anchors {
                verticalCenter: filename.verticalCenter
                right: folderColorRound.left
                rightMargin: 5
            }
        }

        ProgressBar {
            id: progress
            height: 20
            width: 280
            value: model.percent
            background: Rectangle {
                    implicitWidth: 200
                    implicitHeight: 6
                    color: "#cecece"
                    radius: 3
                }

            contentItem: Item {
                implicitWidth: 200
                implicitHeight: 4

                Rectangle {
                    width: parent.parent.visualPosition * parent.width
                    height: parent.height
                    radius: 2
                    color: "#17a81a"
                }
            }
            anchors {
                top: filename.bottom
                topMargin: 10
                left: filename.left
            }
        }

        Text {
            id: percentField
            text: Math.round(model.percent * 100) + "%"
            font.pointSize: 12
            anchors {
                verticalCenter: progress.verticalCenter
                right: pausePlayButton.left
                rightMargin: 5
            }
        }

        TextIconButton {
            id: pausePlayButton
            property bool paused: false
            height: 20
            enabled: model.percent !== 1
            anchors.right: stopButton.left
            anchors.rightMargin: 5
            anchors.verticalCenter: progress.verticalCenter
            ToolTip.visible: hovered
            ToolTip.text: paused ? qsTr("Resume") : qsTr("Pause")
            //fontFamily: fontAwesome.name
            text: paused ? "\uf04b" : "\uf04c"

            onClicked: {
                if (paused) { // start dl
                    paused = false;
                    stopButton.stopped = false
                    console.log("start");
                }
                else {  // pause dl
                    paused = true;
                    console.log("pause");
                }
            }
        }

        TextIconButton {
            id: stopButton
            property bool stopped: false
            height: 15
            enabled: model.percent !== 1 || !stopped
            anchors.right: folderColorRound.left
            anchors.rightMargin: 5
            anchors.verticalCenter: progress.verticalCenter

            ToolTip.visible: hovered
            ToolTip.text: qsTr("Stop")
            text: "\uf04d"

            onClicked: {
                if (!stopped) {
                    stopped = true;
                    pausePlayButton.paused = true
                    console.log("stopping");
                }
            }
        }

        Text {
            id: progressSize
            text: model.cur_size
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 10
            font.pointSize: 10
            anchors.left: filename.left
        }

        Text {
            id: totalProgressSize
            text: " / " + model.total_size
            anchors.verticalCenter: progressSize.verticalCenter
            font.pointSize: 10
            anchors.left: progressSize.right

        }

        Rectangle {
            id: folderColorRound
            width: 10
            color: model.color
            radius: 5

            ToolTip.visible: folderMouseArea.containsMouse
            ToolTip.text: model.folderName

            anchors {
                top: parent.top
                bottom: parent.bottom
                right: parent.right
            }

            MouseArea {
                id: folderMouseArea
                anchors.fill: parent
                hoverEnabled: true
            }

            Rectangle {
                id: folderColor
                x: 5
                y: 0
                color: model.color
                width: parent.radius
                anchors {
                    top: parent.top
                    bottom: parent.bottom
                    right: parent.right
                }
            }
        }
    }
}
