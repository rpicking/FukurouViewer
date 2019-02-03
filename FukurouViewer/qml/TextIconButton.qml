import QtQuick 2.11

import "."

Item {
    id: root
    property alias text : iconText.text
    property alias font : iconText.font.family
    property string textColor : mouseArea.containsMouse ? Styles.highlighted : Styles.accent
    property string backgroundColor : "transparent"
    property string borderColor: "transparent"
    property int verticalOffset : 0
    property int horizontalOffset : 0
    property alias cursorShape: mouseArea.cursorShape
    property alias fontFamily: iconText.font.family
    property alias hovered : mouseArea.containsMouse

    signal clicked(var mouse)
    signal doubleClicked(var mouse)
    signal rightClicked(var mouse)


    height: 25
    width: height

    baselineOffset: 0
    Text {
        id: iconText
        font.family: Fonts.solidIcons
        font.pixelSize: root.height
        color: textColor
        fontSizeMode: Text.Fit
        //minimumPointSize: root.height
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        anchors {
            horizontalCenter: root.horizontalCenter
            horizontalCenterOffset: horizontalOffset
            verticalCenter: root.verticalCenter
            verticalCenterOffset: verticalOffset
        }
    }

    Rectangle {
        border.color: borderColor
        color: backgroundColor
        implicitHeight: root.height
        implicitWidth: root.height
    }

    MouseArea {
        id: mouseArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor

        onClicked: {
            if(mouse.button === Qt.RightButton)
                root.rightClicked(mouse)
            else
                root.clicked(mouse)
        }

        onDoubleClicked: root.doubleClicked(mouse)
    }
}
