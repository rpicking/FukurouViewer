import QtQuick 2.0
import QtQuick.Controls 1.4

Item {
    id: downloadsWrapper
    anchors.fill: parent

    Rectangle {
        id: statusBar
        color: theme.background
        height: 150
        anchors {
            left: parent.left
            right: parent.right
            top: parent.top
        }

        Text {
            id: downloadsLabel
            text: qsTr("Downloads:")
            color: "white"
            font.pixelSize: 16
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.top: parent.top
            anchors.topMargin: 10
        }
        Text {
            id: downloadsField
            text: downloadManager.total_downloads
            color: "white"
            font.pixelSize: 16
            anchors {
                verticalCenter: downloadsLabel.verticalCenter
                left: downloadsLabel.right
                leftMargin: 5
            }
        }
        Text {
            id: runningLabel
            text: qsTr("Running:")
            color: "white"
            font.pixelSize: 16
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.top: downloadsLabel.bottom
            anchors.topMargin: 5
        }
        Text {
            id: runningField
            text: downloadManager.running_downloads
            color: "white"
            font.pixelSize: 16
            anchors {
                verticalCenter: runningLabel.verticalCenter
                left: downloadsField.left
            }
        }
        Text {
            id: totalProgressLabel
            text: qsTr("Progress: ")
            color: "white"
            font.pixelSize: 16
            anchors.left: parent.left
            anchors.leftMargin: 10
            anchors.top: runningLabel.bottom
            anchors.topMargin: 5
        }

        Text {
            id: curProgress
            text: downloadManager.current_progress
            color: "white"
            font.pixelSize: 16
            anchors {
                verticalCenter: totalProgressLabel.verticalCenter
                left: downloadsField.left
            }
        }

        Text {
            id: totalSize
            text: " / " + downloadManager.total_progress
            color: "white"
            font.pixelSize: 16
            anchors {
                verticalCenter: curProgress.verticalCenter
                left: curProgress.right
            }

        }

        Text {
            id: totalSpeedLabel
            text: qsTr("Speed:")
            color: "white"
            font.pixelSize: 16
            anchors {
                left: parent.horizontalCenter
                verticalCenter: downloadsLabel.verticalCenter
            }
        }
        Text {
            id: totalSpeedField
            text: downloadManager.speed
            color: "white"
            font.pixelSize: 16
            anchors {
                verticalCenter: totalSpeedLabel.verticalCenter
                left: totalSpeedLabel.right
                leftMargin: 5
            }
        }

        Text {
            id: etaLabel
            text: qsTr("ETA:")
            color: "white"
            font.pixelSize: 16
            anchors {
                left: parent.horizontalCenter
                verticalCenter: runningLabel.verticalCenter
            }
        }
        Text {
            id: etaField
            text: "~2hr 4min 13sec"
            color: "white"
            font.pixelSize: 16
            anchors {
                verticalCenter: etaLabel.verticalCenter
                left: etaLabel.right
                leftMargin: 5
            }
        }

        ProgressBar {
            id: totalProgressBar
            value: downloadManager.percent
            height: 15
            anchors {
                left: parent.left
                leftMargin: 10
                right: parent.right
                rightMargin: 10
                bottom: parent.bottom
                bottomMargin: 20
            }
        }
    }

    ScrollView {
        anchors {
            top: statusBar.bottom
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }
        ListView {
            id: downloadsView
            anchors.fill: parent
            model: downloadsModel
            interactive: true
            //enabled: false
            delegate: DownloadItem{}
            spacing: 6
            snapMode: ListView.NoSnap
            clip: true
        }
    }
}
