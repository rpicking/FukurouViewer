import QtQuick 2.0
import QtGraphicalEffects 1.0
import QtQuick.Controls 2.1
//import QtQml 2.2

//Item {
Component {
    Rectangle {
        id: root
        height: 60
        anchors.right: parent.right
        anchors.rightMargin: 6
        anchors.left: parent.left
        anchors.leftMargin: 0
        //border.width: 1

        property bool expanded : false

        onActiveFocusChanged: {
            if (activeFocus) {
                state = "enlarge";
            }
            else {
                state = "";
            }
        }

        MouseArea {
            anchors.fill: parent
            propagateComposedEvents: true

            onClicked: {
                if (root.activeFocus) {
                    thumbnail.forceActiveFocus();
                }
                else {
                    root.forceActiveFocus();
                }
            }
        }

        Image {
            id: thumbnail
            height: 30
            width: height
            anchors.verticalCenter: parent.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 10
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

        Rectangle {
            id: rightSeparator
            anchors {
                top: parent.top
                bottom: parent.bottom
                left: thumbnail.right
                leftMargin: 10
            }
            width: 1
            color: "lightgrey"
        }

        Text {
            id: filename
            text: model.filename
            font.weight: Font.DemiBold
            elide: Text.ElideRight
            color: model.dead ? "grey" : "#0009d6"
            font.strikeout: model.dead
            anchors.left: rightSeparator.right
            anchors.leftMargin: 10
            anchors.right: deleteButton.left
            anchors.rightMargin: 0
            anchors.verticalCenter: parent.verticalCenter

            MouseArea {
                id: filenameMouseArea
                visible: false //!model.dead
                width: parent.contentWidth
                anchors {
                    left: parent.left
                    top: parent.top
                    bottom: parent.bottom
                }

                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    console.log("open file in default application");
                    mainWindow.openItem(model.full_path, "file");
                }
            }
        }

        Text {
            id: urlLink
            visible: false
            text: model.src_url
            font.pointSize: 10
            color: "grey"
            elide: Text.ElideRight
            anchors.left: rightSeparator.right
            anchors.leftMargin: 15
            anchors.right: deleteButton.left
            anchors.top: filename.bottom
            anchors.topMargin: 5

            MouseArea {
                visible: true
                width: parent.contentWidth
                anchors {
                    left: parent.left
                    top: parent.top
                    bottom: parent.bottom
                }
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    console.log("open url in default browser");
                    mainWindow.openItem(model.src_url, "url");
                }
            }
        }

        Text {
            id: showFolder
            visible: false
            text: model.dead ? "Deleted" : "Show in folder"
            //font.pointSize: 12
            color: model.dead ? "grey" : "#0009d6"
            font.bold: model.dead ? true : false
            anchors.left: rightSeparator.right
            anchors.leftMargin: 15
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 10

            MouseArea {
                anchors.fill: parent
                cursorShape: Qt.PointingHandCursor
                onClicked: {
                    console.log("opening folder location");
                     mainWindow.openItem(model.full_path, "folder");
                }
            }
        }

        TextIconButton {
            id: deleteButton
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
                //console.log(model.id);
                mainWindow.deleteHistoryItem(model.id);
            }
        }

        Rectangle {
            id: bottomSeparator
            anchors {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
            }
            height: 1
            color: "lightgrey"
        }

        DropShadow {
            anchors.fill: bottomSeparator
            horizontalOffset: 0
            verticalOffset: 2
            radius: 8.0
            samples: 7
            color: "#80000000"
            source: bottomSeparator
        }

        states: [
            State {
                name: "enlarge"
                PropertyChanges {
                    target: root
                    height: 100
                }
                AnchorChanges {
                    target: filename
                    anchors.verticalCenter: undefined
                    anchors.top: parent.top
                }
                PropertyChanges {
                    target: filename
                    anchors.topMargin: 5
                }
                PropertyChanges {
                    target: filenameMouseArea
                    visible: !model.dead
                }

                PropertyChanges {
                    target: urlLink
                    visible: true
                }
                PropertyChanges {
                    target: showFolder
                    visible: true
                }
                AnchorChanges {
                    target: thumbnail
                    anchors.left: parent.left
                }
                PropertyChanges {
                    target: thumbnail
                    anchors.leftMargin: 10
                }
                AnchorChanges {
                    target: deleteButton
                    anchors.verticalCenter: undefined
                    anchors.top: parent.top
                }
                PropertyChanges {
                    target: deleteButton
                    anchors.topMargin: 5
                }
            },
            State {
                name: "shrink"
                StateChangeScript {
                    name: "shrinkScript"
                    script: {
                        //thumbnail.forceActiveFocus();
                    }
                }
            }
        ]
    }
}
