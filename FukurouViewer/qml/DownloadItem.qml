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

        property bool paused: false
        property bool stopped: false

        function togglePause() {
            if (stopped) {
                console.log("resume" + model.id);
                stopped = false;
                paused  = false;
                resume();
                return;
            }

            if (paused) { // unpause
                paused = false;
                console.log("unpause " + model.id);
            } else { // pause dl
                paused = true;
                console.log("pause " + model.id);
            }

            mainWindow.downloader_task(model.id, "pause");
        }

        function stop() {
            stopped = true;
            paused = true;
            console.log("stopping " + model.id);
            mainWindow.downloader_task(model.id, "stop");
        }

        function resume() {
            mainWindow.resume_download(model.id);
        }

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
            text: model.speed ? model.speed + "/s" : ""
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
            //width: 280
            value: model.percent
            to: 100
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
                right: percentField.left
                rightMargin: 10
            }
        }

        Text {
            id: percentField
            width: 43
            text: model.percent + "%"
            font.pointSize: 12
            anchors {
                verticalCenter: progress.verticalCenter
                right: pausePlayButton.left
                rightMargin: 5
            }
        }

        TextIconButton {
            id: pausePlayButton

            height: 20
            enabled: model.percent !== 100
            anchors.right: stopButton.left
            anchors.rightMargin: 5
            anchors.verticalCenter: progress.verticalCenter
            ToolTip.visible: hovered
            ToolTip.text: paused ? qsTr("Resume") : qsTr("Pause")
            //fontFamily: fontAwesome.name
            text: paused ? "\uf04b" : "\uf04c"

            onClicked: {
                togglePause();
            }
        }

        TextIconButton {
            id: stopButton
            height: 15
            enabled: model.percent !== 100 && !stopped
            anchors.right: folderColorRound.left
            anchors.rightMargin: 5
            anchors.verticalCenter: progress.verticalCenter

            ToolTip.visible: hovered && enabled
            ToolTip.text: qsTr("Stop")
            text: "\uf04d"

            onClicked: {
                stop();
            }
        }

        Text {
            id: curSize
            text: model.cur_size
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 10
            font.pointSize: 10
            anchors.left: filename.left
        }

        Text {
            id: totalSize
            text: " / " + model.total_size
            anchors.verticalCenter: curSize.verticalCenter
            font.pointSize: 10
            anchors.left: curSize.right

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
