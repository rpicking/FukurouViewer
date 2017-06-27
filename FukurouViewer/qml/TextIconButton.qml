import QtQuick 2.0
import QtQuick.Controls 2.1

Rectangle {
    property alias buttonText : textField.text
    property alias fontFamily : textField.font.family
    property alias mouseArea : iconButtonMouseArea

    width: 25
    height: 25
    color: "transparent"
    radius: 5
    ToolTip.visible: iconButtonMouseArea.containsMouse
    ToolTip.text: qsTr("")
    Text {
        id: textField
        color: iconButtonMouseArea.containsMouse ? theme.highlighted : theme.accent
        font.pointSize: 20
        //font.family: fontAwesome.name
        anchors.verticalCenterOffset: 1
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.verticalCenter: parent.verticalCenter
    }

    MouseArea {
        id: iconButtonMouseArea
        anchors.fill: parent
        hoverEnabled: true
        //onClicked: {}
    }
}
