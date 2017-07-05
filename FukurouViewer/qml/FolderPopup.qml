import QtQuick 2.0
import QtQuick.Window 2.2
import QtQuick.Controls 2.1
import QtQuick.Dialogs 1.2

Window {
    id: newFolderWindow
    flags: Qt.FramelessWindowHint //| Qt.WindowStaysOnTopHint
    width: 450
    height: 250

    property bool validFolder: true

    Component.onCompleted: {
        mainWindow.receiveValidFolder.connect(validFolderCheck);
    }

    onVisibleChanged: {
        if(visible){
            colorField.color = Qt.rgba(Math.random(), Math.random(), Math.random(), 1);
        }
    }

    function clearValues() {
        nameInput.text = "";
        folderInput.text = "";
    }

    function validFolderCheck(valid) {
        validFolder = valid;
        validFolderField.visible = true;
    }

    MouseArea {
        anchors.fill: parent
        propagateComposedEvents: true
        property point clickPos: Qt.point(1,1)

        onPressed: {
            clickPos  = Qt.point(mouse.x,mouse.y)
            header.forceActiveFocus();
        }

        onPositionChanged: {
            var delta = Qt.point(mouse.x-clickPos.x, mouse.y-clickPos.y)
            newFolderWindow.x += delta.x;
            newFolderWindow.y += delta.y;
        }
    }

    Rectangle {
        id: header
        height: 40
        anchors.right: parent.right
        anchors.left: parent.left
        anchors.top: parent.top
        color: theme.background

        Text {
            text: "Add Favorite Folder"
            font.family: "Verdana"
            font.pointSize: 17
            color: theme.foreground
            anchors.top: parent.top
            anchors.topMargin: 6
            anchors.left: parent.left
            anchors.leftMargin: 14
        }
    }

    Rectangle {
        id: content
        anchors.bottom: footer.top
        anchors.bottomMargin: 0
        anchors.rightMargin: 10
        anchors.leftMargin: 10
        anchors.top: header.bottom
        anchors.right: parent.right
        anchors.left: parent.left
        anchors.topMargin: 10
        Text {
            id: nameLabel
            text: qsTr("Name")
            anchors.verticalCenter: nameField.verticalCenter
            anchors.horizontalCenter: browseButton.horizontalCenter
            font.pixelSize: 18
        }

        Rectangle {
            id: nameField
            height: 30
            anchors.top: parent.top
            anchors.topMargin: 0
            anchors.leftMargin: 0
            anchors.right: parent.right
            anchors.rightMargin: 0
            anchors.left: folderField.left
            MouseArea {
                propagateComposedEvents: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                anchors.fill: parent
                onClicked: {
                    if (mouse.button === Qt.RightButton) {
                        nameMenu.open();
                    }
                }
            }

            TextInput {
                id: nameInput
                anchors.right: parent.right
                anchors.left: parent.left
                selectByMouse: true
                font.family: "Verdana"
                clip: true
                anchors.leftMargin: 5
                font.pixelSize: 16
                anchors.verticalCenter: parent.verticalCenter
                persistentSelection: true

                Menu {
                    id: nameMenu
                    title: "Edit"

                    MenuItem {
                        text: "Cut"
                        onTriggered: nameInput.cut()
                    }

                    MenuItem {
                        text: "Copy"
                        onTriggered: nameInput.copy()
                    }

                    MenuItem {
                        text: "Paste"
                        onTriggered: nameInput.paste()
                    }
                }
            }
            border.width: 1
        }

        Button {
            id: browseButton
            width: 70
            height: 40
            text: qsTr("Browse")
            padding: 6
            anchors.verticalCenter: folderField.verticalCenter
            anchors.left: parent.left
            anchors.leftMargin: 0
            checkable: false

            onClicked: fileDialog.visible = true;
        }

        Rectangle {
            id: validFolderField
            x: 80
            y: 40
            width: 30
            height: 30
            color: "#ffffff"
            visible: false
            anchors.verticalCenter: folderField.verticalCenter
            anchors.right: parent.right
            anchors.rightMargin: 0

            onVisibleChanged: {
                if(visible) {
                    folderField.state = "containsText"
                }
                else {
                    folderField.state = "default"
                }
            }

            Text {
                text: validFolder ? "\uf058" : "\uf057"
                color: validFolder ? "green" : "red"
                font.family: fontAwesome.name
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                anchors.fill: parent
                font.pixelSize: 20
            }
        }

        Rectangle {
            id: folderField
            height: 30
            anchors.top: nameField.bottom
            anchors.topMargin: 10
            anchors.left: browseButton.right
            anchors.leftMargin: 10
            anchors.right: parent.right
            anchors.rightMargin: 0
            border.width: 1

            MouseArea {
                anchors.fill: parent
                propagateComposedEvents: true
                acceptedButtons: Qt.LeftButton | Qt.RightButton
                onClicked: {
                    if (mouse.button === Qt.RightButton) {
                        menu.open();
                    }
                }
            }

            states: [
                State {
                    name: "default"
                    AnchorChanges { target: folderField; anchors.right: parent.right }
                },
                State {
                    name:"containsText"
                    AnchorChanges { target: folderField; anchors.right: validFolderField.left }
                }
            ]

            transitions: Transition {
                AnchorAnimation {
                    easing.type: Easing.OutQuad
                    duration: 250
                }
            }

            TextInput {
                id: folderInput
                anchors.leftMargin: 5
                anchors.verticalCenter: parent.verticalCenter
                anchors.right: parent.right
                anchors.left: parent.left
                clip: true
                selectByMouse: true
                font.family: "Verdana"
                font.pixelSize: 16
                persistentSelection: true

                onActiveFocusChanged: {
                    if(!activeFocus) {
                        if(text !== "") {
                            mainWindow.requestValidFolder(folderInput.text);
                        }
                        else {
                            validFolderField.visible = false;
                        }
                    }
                }

                Menu {
                    id: menu
                    title: "Edit"

                    MenuItem {
                        text: "Cut"
                        onTriggered: parent.cut()
                    }

                    MenuItem {
                        text: "Copy"
                        onTriggered: parent.copy()
                    }

                    MenuItem {
                        text: "Paste"
                        onTriggered: parent.paste()
                    }
                }
            }
        }


        FileDialog {
            id: fileDialog
            title: "Please choose a folder"
            visible: false
            folder: shortcuts.home
            selectFolder: true
            selectMultiple: false
            onAccepted: {
                var path = fileDialog.fileUrl.toString();
                //console.log(path);
                // remove prefixed "file:///"
                path = path.replace(/^(file:\/{3})/,"");
                // unescape html codes like '%23' for '#'
                var cleanPath = decodeURIComponent(path);
                folderInput.text = cleanPath;
                if(nameInput.text === "") {
                    nameInput.text = cleanPath.replace(/\\/g,'/').replace(/.*\//, '');
                }
                mainWindow.requestValidFolder(folderInput.text);
            }
            onRejected: {
                console.log("Canceled")
            }
        }

        Text {
            id: colorLabel
            text: qsTr("Color")
            anchors.top: browseButton.bottom
            anchors.topMargin: 10
            anchors.horizontalCenter: browseButton.horizontalCenter
            font.pixelSize: 18
        }

        Rectangle {
            id: colorField
            width: 30
            height: 30
            color: "#ffffff"
            anchors.top: folderField.bottom
            anchors.topMargin: 10
            anchors.left: folderField.left
            anchors.leftMargin: 0
            border.width: 1

            MouseArea {
                anchors.fill: parent
                onClicked: {
                    colorDialog.color = colorField.color;
                    colorDialog.open();
                }
            }
        }

        ColorDialog {
            id: colorDialog
            //visible: false
            title: "Please choose a color"
            //color: "red"
            showAlphaChannel: false
            onAccepted: {
                console.log("You chose: " + colorDialog.color)
                colorField.color = colorDialog.color;
            }
            onRejected: {
                console.log("Canceled")
            }
            //Component.onCompleted: visible = true
        }


    }

    Rectangle {
        id: footer
        height: 60
        anchors.rightMargin: 10
        anchors.leftMargin: 10
        anchors.bottomMargin: 10
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.left: parent.left

        Rectangle {
            id: saveButton
            width: 70
            height: 40
            radius: 5
            color: {
                if(saveMA.containsPress) {
                    return "#bcbcbc";
                }
                else if (saveMA.containsMouse) {
                    return "#e0e0e0";
                }
                return "#ffffff";
            }
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 10
            anchors.right: cancelButton.left
            anchors.rightMargin: 20

            Text {
                id: saveText
                text: qsTr("SAVE")
                font.bold: true
                font.pixelSize: 16
                font.family: "Verdana"
                anchors.horizontalCenter: parent.horizontalCenter
                anchors.verticalCenter: parent.verticalCenter
                color: theme.accent
            }

            MouseArea {
                id: saveMA
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    mainWindow.createFavFolder(nameInput.text, folderInput.text, colorField.color, 2);
                    clearValues();
                    newFolderWindow.close();
                }
            }
        }

        Rectangle {
            id: cancelButton
            width: cancelText.width + 10
            height: 40
            radius: 5
            color: {
                if(cancelMA.containsPress) {
                    return "#bcbcbc";
                }
                else if (cancelMA.containsMouse) {
                    return "#e0e0e0";
                }
                return "#ffffff";
            }
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 10
            anchors.right: parent.right
            anchors.rightMargin: 10

            Text {
                id: cancelText
                text: qsTr("CANCEL")
                font.bold: true
                font.pixelSize: 16
                font.family: "Verdana"
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
                color: theme.accent
            }

            MouseArea {
                id: cancelMA
                anchors.fill: parent
                hoverEnabled: true
                onClicked: {
                    clearValues();
                    newFolderWindow.close();
                }
            }
        }
    }
}
