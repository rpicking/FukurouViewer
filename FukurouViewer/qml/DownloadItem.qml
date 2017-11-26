import QtQuick 2.0
import QtQuick.Controls 1.4

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
                right: parent.right
                rightMargin: 15
            }
        }

        Text {
            id: progressSize
            text: model.cur_size
            font.pointSize: 10
            anchors {
                top: progress.bottom
                topMargin: 10
                left: filename.left
            }
        }
        Text {
            id: totalProgressSize
            text: " / " + model.total_size
            font.pointSize: 10
            anchors {
                top: progress.bottom
                topMargin: 10
                left: progressSize.right
            }
        }

        Rectangle {
            id: folderColorRound
            width: 10
            color: model.color
            radius: 5
            anchors {
                top: parent.top
                bottom: parent.bottom
                right: parent.right
            }
        }
        Rectangle {
            id: folderColor
            color: model.color
            width: folderColorRound.radius
            anchors {
                top: folderColorRound.top
                bottom: folderColorRound.bottom
                right: folderColorRound.right
            }
        }
    }
}
