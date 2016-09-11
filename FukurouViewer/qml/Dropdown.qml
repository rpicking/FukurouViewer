import QtQuick 2.5
import QtGraphicalEffects 1.0

Item {
    id: dropdown

    property Item son
    width: 0
    height: 0
    visible: false
    MouseArea {
        id: mouseArea
        anchors.fill: parent
        onClicked: {
            dropdown.forceActiveFocus()
        }
    }

    Rectangle {
        id: background
        anchors.fill: parent
        color: "#001f8d"
    }

    states: [
        State {
            name: "open"
            when: (activeFocus == true)
            PropertyChanges {
                target: dropdown
                width: son.width
                height: son.width
                visible: true
            }
        },
        State {
            name: "close"
            when: (activeFocus == false)
            PropertyChanges {
                target: dropdown
                width: 0
                height: 0
                visible: false
            }
        }
    ]
    transitions: [
        Transition {
            from: "*"; to: "open"
            NumberAnimation {
                easing.type: Easing.Linear
                properties: "width,height,visible";
                duration: 1000
            }
        },
        Transition {
            from: "*"; to: "close"
            NumberAnimation {
                easing.type: Easing.Linear
                properties: "width,height,visible";
                duration: 1000
            }
        }
    ]
}
