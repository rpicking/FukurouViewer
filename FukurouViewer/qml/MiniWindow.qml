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
        mainWindow.requestHistory(0);   //0 = get all history
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

            TextIconButton {
                id: viewFolderList
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                ToolTip.text: qsTr("View favorite folders")
                fontFamily: fontAwesome.name
                buttonText: "\uf07c"
                mouseArea.onClicked: {
                    console.log("Viewing folders");
                }
            }

            TextIconButton {
                id: addNewFavFolder
                Layout.alignment: Qt.AlignRight | Qt.AlignVCenter
                ToolTip.text: qsTr("Add new save folder")
                fontFamily: fontAwesome.name
                buttonText: "\uf067"
                mouseArea.onClicked: {
                    folderPopup.visible = true;
                }
            }
        }
    }

    FolderPopup {
        id: folderPopup
        visible: false
    }

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
