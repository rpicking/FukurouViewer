import QtQuick 2.0
import QtQuick.Controls 2.1
import QtQuick.Controls 1.4

Item {
    //Component {
    width: 400
    height: 100
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
            value: model.percent
            anchors {
                top: filename.bottom
                topMargin: 10
                left: filename.left
                right: percentField.left
                rightMargin: 10
            }
        }

        Text {
            id: percentField
            text: Math.round(model.percent * 100) + "%"
            font.pointSize: 10
            anchors {
                verticalCenter: progress.verticalCenter
                right: pauseButton.left
                rightMargin: 5
            }
        }

        TextIconButton {
            id: pauseButton
            property bool paused: false
            enabled: model.percent !== 1
            anchors.right: parent.right
            anchors.rightMargin: 15
            anchors.verticalCenter: progress.verticalCenter
            ToolTip.visible: this.mouseArea.containsMouse
            ToolTip.text: paused ? qsTr("Resume") : qsTr("Pause")
            fontFamily: fontAwesome.name
            buttonText: paused ? "\uf04b" : "\uf04c"

            mouseArea.onClicked: {
                if (paused) {
                    paused = false;
                }
                else {
                    paused = true;
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
