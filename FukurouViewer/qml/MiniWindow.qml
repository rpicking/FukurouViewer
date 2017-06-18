import QtQuick 2.0
import QtQuick.Window 2.2

Window {
    id: window
    //visible: false
    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    width: 400
    height: 640

    Component.onCompleted: {
        mainWindow.receiveHistory.connect(setHistory)
        mainWindow.onWindowClose.connect(closeWindow)
    }

    function openWindow(_x, _y) {
        show();
        x = _x - width;
        y = _y - height;
        mainWindow.requestHistory();
    }

    function closeWindow() {
        hide();
    }

    function setHistory(items) {
        for(var i = 0; i < items.length; ++i) {
            listModel.append(items[i]);
        }
    }

    ListModel {
        id: listModel
    }

    ListView {
        id: listView
        anchors.top: textEdita.bottom
        anchors.right: parent.right
        anchors.bottom: parent.bottom
        anchors.left: parent.left
        anchors.topMargin: 0
        model: listModel

        delegate: Text {
            text: filename

        }
    }

    TextEdit {
        id: textEdita
        text: qsTr("MINI MAN")
        x: 500
        y: 500
        anchors.left: parent.left
        anchors.leftMargin: 15
        anchors.top: parent.top
        anchors.topMargin: 15
        font.pointSize: 17
        font.underline: true
        verticalAlignment: Text.AlignVCenter
        anchors.horizontalCenter: parent.horizontalCenter
    }


}
