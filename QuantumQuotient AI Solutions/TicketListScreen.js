// TicketListScreen.js
import React, { useEffect, useState } from "react";
import { View, Text, FlatList, TouchableOpacity } from "react-native";

const API = "http://YOUR_SERVER:5000/api";

export default function TicketListScreen({ navigation }) {
  const [tickets, setTickets] = useState([]);

  useEffect(() => {
    fetch(`${API}/tickets`)
      .then(res => res.json())
      .then(setTickets)
      .catch(console.error);
  }, []);

  return (
    <View style={{ flex: 1, padding: 16 }}>
      <Text style={{ fontSize: 24, marginBottom: 12 }}>Tickets</Text>
      <FlatList
        data={tickets}
        keyExtractor={item => item.id.toString()}
        renderItem={({ item }) => (
          <TouchableOpacity
            onPress={() => navigation.navigate("TicketDetail", { id: item.id })}
            style={{ paddingVertical: 10, borderBottomWidth: 0.5 }}
          >
            <Text>#{item.id} [{item.priority}]</Text>
            <Text>{item.subject}</Text>
          </TouchableOpacity>
        )}
      />
    </View>
  );
}
