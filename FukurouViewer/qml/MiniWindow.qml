import QtQuick 2.0
import QtQuick.Window 2.2
import QtQuick.Dialogs 1.2
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.1
import QtQuick.Controls.Styles 1.4

import "controls" as Awesome

Window {
    id: window
    //visible: false
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    width: 400
    height: 640

    Component.onCompleted: {
        mainWindow.receiveHistory.connect(setHistory);
        mainWindow.onWindowClose.connect(closeWindow);
    }

    onActiveChanged: {
        if(!active && (folderPopup.visible === false)) {
            closeWindow();
        }
    }

    function openWindow(_x, _y) {
        show();
        x = _x - width;
        y = _y - height;
        // mainWindow.requestHistory();
        requestActivate();
        mainWindow.requestHistory();
        //console.log(active);
    }

    function closeWindow() {
        hide();
    }

    function setHistory(items) {
        historyModel.clear();
        for(var i = 0; i < items.length; ++i) {
            historyModel.append(items[i]);
        }
        //historyModel.append({"itemtype": "end"})
    }

    // dont need this here.  only to view in qtcreator design
    /*FontLoader {
        id: fontAwesome
        source: "fonts/fontawesome-webfont.ttf"
    }*/

    Rectangle {
        id: topBar
        height: 40
        color: theme.background
        anchors.top: parent.top
        anchors.topMargin: 0
        anchors.left: parent.left
        anchors.leftMargin: 0
        anchors.right: parent.right
        anchors.rightMargin: 0


        RowLayout {
            anchors.rightMargin: 5
            anchors.leftMargin: 5
            spacing: 2
            anchors.fill: parent

            Text {
                id: titleText
                height: 28
                color: theme.foreground
                text: qsTr("Fukurou Downloader")
                font.family: "Verdana"
                font.pointSize: 17
                verticalAlignment: Text.AlignVCenter
            }

            Rectangle {
                id: addNewFavFolder
                width: 25
                height: 25
                color: "transparent"
                radius: 5
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                ToolTip.visible: addFavFolderMouseArea.containsMouse
                ToolTip.text: qsTr("Add new save folder")
                Text {
                    color: addFavFolderMouseArea.containsMouse ? theme.highlighted : theme.accent
                    font.pointSize: 20
                    font.family: fontAwesome.name
                    text: "\uf067"
                    anchors.verticalCenterOffset: 1
                    anchors.horizontalCenter: parent.horizontalCenter
                    anchors.verticalCenter: parent.verticalCenter
                }

                MouseArea {
                    id: addFavFolderMouseArea
                    anchors.fill: parent
                    hoverEnabled: true

                    onClicked: {
                        folderPopup.visible = true
                        //newFolderdialog.visible = true;
                    }
                }
            }
        }
    }

    FolderPopup {
        id: folderPopup
        visible: false
    }

    /*Dialog {
        id: newFolderdialog
        visible: false
        width: 400
        title: "Add Favorite Folder"
        standardButtons: Dialog.Save | Dialog.Cancel

        onAccepted: console.log("Ok clicked")
        onRejected: console.log("Cancel clicked")

        //contentItem: FolderPopup {}
    }*/

    ListView {
        id: historyView
        anchors.top: topBar.bottom
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.topMargin: 0
        model: historyModel
        //enabled: false
        ScrollBar.vertical: ScrollBar {
            id: historyScrollbar
            //policy: ScrollBar.AlwaysOn    Qt 5.9
        }
        delegate: HistoryItem{}
        snapMode: ListView.NoSnap
        footer: seeMoreButton
        clip: true
    }

    ListModel {
        id: historyModel
    }

    Component {
        id: seeMoreButton
        Rectangle {
            height: 50
            anchors.right: parent.right
            anchors.rightMargin: 15
            anchors.left: parent.left
            anchors.leftMargin: 0
            Text {
                anchors.verticalCenter: parent.verticalCenter
                anchors.horizontalCenter: parent.horizontalCenter
                font.underline: true
                text: qsTr("SEE MORE")
            }
        }
    }
}
