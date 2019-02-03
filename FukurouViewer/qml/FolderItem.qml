import QtQuick 2.11

Component {
    id: dragDelegate

    MouseArea {
        id: dragArea

        property ListView _listView: ListView.view

        property int index: model.index
        property bool held: false
        anchors { left: parent.left; right: parent.right }
        height: content.height

        drag.target: held ? content : undefined
        drag.axis: Drag.YAxis

        pressAndHoldInterval: 250
        onPressAndHold: held = true
        onReleased: {
            held = false;
            console.log("UPDATE IN DB");
        }

        Rectangle {
            id: content

            Drag.active: dragArea.held
            Drag.source: dragArea
            Drag.hotSpot.x: width / 2
            Drag.hotSpot.y: height / 2

            anchors {
                horizontalCenter: parent.horizontalCenter
                verticalCenter: parent.verticalCenter
            }
            width: dragArea.width; height: 80
            color: dragArea.held ? "lightsteelblue" : "white"
            Behavior on color { ColorAnimation { duration: 100 } }
            radius: 2
            states: State {
                when: dragArea.held

                ParentChange { target: content; parent: foldersTab }
                AnchorChanges {
                    target: content
                    anchors { horizontalCenter: undefined; verticalCenter: undefined }
                }
            }

            Text {
                id: nameField
                text: model.name
                font.pointSize: 16
                wrapMode: Text.WordWrap
                anchors {
                    top: parent.top
                    topMargin: 10
                    left: parent.left
                    leftMargin: 10
                }


            }

            Text {
                id: pathField
                text: model.path
                font.pointSize: 8
                font.italic: true
                anchors {
                    top: nameField.bottom
                    topMargin: 15
                    left: nameField.left
                    leftMargin: 20
                }
            }

            Rectangle {
                id: colorBox
                width: height
                color: model.color
                border.width: 1
                anchors {
                    top: parent.top
                    topMargin: 10
                    bottom: parent.bottom
                    bottomMargin: 10
                    right: parent.right
                    rightMargin: 5
                }
            }

            // Bottom line separator
            Rectangle {
                height: 1
                color: "lightgrey"
                anchors {
                    left: parent.left
                    right: parent.right
                    bottom: parent.bottom
                }
            }
        }

        DropArea {
            anchors { fill: parent; margins: 10 }

            onEntered: {
                _listView.model.move(drag.source.index, dragArea.index, 1);
            }
        }
    }
}

