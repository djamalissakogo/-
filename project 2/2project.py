import networkx as nx
import matplotlib.pyplot as plt
from vk_api.exceptions import ApiError
import vk_api
import time

def getFriendsInfo(vk, user_id, max_friends=None, delay_between_requests=0.36):
    try:
        friends = vk.friends.get(user_id=user_id, fields="bdate,city")['items']
        friends_data = []
        processed_ids = set()
        friend_ids = set()

        for friend in friends:
            friend_id = friend['id']
            name = f"{friend['first_name']} {friend['last_name']}"
            age = friend.get('bdate', 'N/A')
            city = friend.get('city', {}).get('title', 'N/A')
            friends_data.append({'id': friend_id, 'name': name, 'age': age, 'city': city, 'level': 1})
            processed_ids.add(friend_id)
            friend_ids.add(friend_id)

        if max_friends is None or max_friends > len(friends):
            max_friends = len(friends)

        edges = []

        for friend in friends[:max_friends]:
            friend_id = friend['id']
            friend_name = f"{friend['first_name']} {friend['last_name']}"
            try:
                time.sleep(delay_between_requests)  # ограничиваем запросы
                friends_of_friend = vk.friends.get(user_id=friend_id, fields="bdate,city")['items']
                for fof in friends_of_friend:
                    fof_id = fof['id']
                    if fof_id not in processed_ids:
                        name = f"{fof['first_name']} {fof['last_name']}"
                        age = fof.get('bdate', 'N/A')
                        city = fof.get('city', {}).get('title', 'N/A')
                        friends_data.append({'id': fof_id, 'name': name, 'age': age, 'city': city, 'level': 2})
                        processed_ids.add(fof_id)
                    else:
                        name = next((item['name'] for item in friends_data if item['id'] == fof_id), None) # имя друга
                    edges.append((friend_id, fof_id))
            except ApiError:
                pass

            edges.append((user_id, friend_id)) # связь между пользователем и другом

        return friends_data, edges, friend_ids

    except ApiError:
        return [], [], set()

def createSocialGraph(friends_data, edges, user_id):
    G = nx.Graph()
    id_to_name = {friend['id']: friend['name'] for friend in friends_data}
    level_dict = {friend['name']: friend['level'] for friend in friends_data}

    for friend in friends_data:
        G.add_node(friend['name'], age=friend['age'], city=friend['city'], level=friend['level'])

    user_name = '123qwe'
    G.add_node(user_name, level=0)

    id_to_name[user_id] = user_name

    for edge in edges:
        node1_name = id_to_name.get(edge[0])
        node2_name = id_to_name.get(edge[1])
        if node1_name and node2_name and node1_name != node2_name:
            G.add_edge(node1_name, node2_name)

    return G

def plotGraph(G, show_labels=True, num_top_nodes=None, total_friends=0, total_friends_of_friends=0):
    pos = nx.spring_layout(G, k=0.1, iterations=50)

    betweenness = nx.betweenness_centrality(G)
    closeness = nx.closeness_centrality(G)
    eigenvector = nx.eigenvector_centrality(G, max_iter=1000)

    node_sizes = 50  # размер кружочков
    node_colors = [closeness[node] for node in G.nodes()]

    fig, ax = plt.subplots(figsize=(16, 9), constrained_layout=True)

    nx.draw(
        G, pos, with_labels=show_labels, node_size=node_sizes, node_color=node_colors,
        cmap=plt.cm.viridis, edge_color='gray', font_size=8 if show_labels else 0, ax=ax
    )

    plt.title(f"Социальный граф\nВсего друзей: {total_friends}, друзей друзей: {total_friends_of_friends}\nУзлов: {len(G.nodes())}, Рёбер: {len(G.edges())}")

    # colorbar
    # sm = plt.cm.ScalarMappable(cmap=plt.cm.viridis, norm=plt.Normalize(vmin=min(node_colors), vmax=max(node_colors)))
    # sm.set_array([])
    # cbar = plt.colorbar(sm, ax=ax)
    # cbar.set_label("Центральность близости", fontsize=12)
    # cbar.set_ticks([min(node_colors), (min(node_colors) + max(node_colors))/2, max(node_colors)])
    # cbar.set_ticklabels([f"{min(node_colors):.2f}", f"{(min(node_colors) + max(node_colors))/2:.2f}", f"{max(node_colors):.2f}"])

    mng = plt.get_current_fig_manager()
    try:
        mng.window.state('zoomed')
    except AttributeError:
        pass

    plt.show()

    print(f"\nВсего друзей: {total_friends}")
    print(f"Всего друзей друзей: {total_friends_of_friends}")
    print(f"Общее количество узлов в графе: {len(G.nodes())}")
    print(f"Общее количество ребер в графе: {len(G.edges())}")

    if num_top_nodes is not None:
        num_top_nodes = int(num_top_nodes)
    else:
        num_top_nodes = len(G.nodes())

    print("\nЦентральность посредничества:")
    sorted_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)
    for name, centrality in sorted_betweenness[:num_top_nodes]:
        print(f"{name}: {centrality:.4f}")

    print("\nЦентральность близости:")
    sorted_closeness = sorted(closeness.items(), key=lambda x: x[1], reverse=True)
    for name, centrality in sorted_closeness[:num_top_nodes]:
        print(f"{name}: {centrality:.4f}")

    print("\nСобственная центральность:")
    sorted_eigenvector = sorted(eigenvector.items(), key=lambda x: x[1], reverse=True)
    for name, centrality in sorted_eigenvector[:num_top_nodes]:
        print(f"{name}: {centrality:.4f}")

def main():
    token = "vk1.a.kEMv5kD34-iItjv29fOpHKDFXR11BoAzgSEOFtSBAB9n01qnraENy9emYjclvQJmEXlYZiJfz-LH8V3pZ6xo3GODJ4Rtk0VEurF7ryHPDCcn99ShlIvvvZRljW7LMNQp4kn54_ep3rkhl82rxM_y9ah6RdGALjZGTiOOsCYu5WJ98qfvXDQTYiW8bGYZyiP82eZr2iYEibuFkgUtnOuqjw"
    vk_session = vk_api.VkApi(token=token)
    vk = vk_session.get_api()
    user_id = "547740648"

    delay_between_requests = 0.33

    max_friends_input = input("Сколько друзей или 'all': ")
    if max_friends_input.lower() == 'all':
        max_friends = None
    else:
        try:
            max_friends = int(max_friends_input)
        except ValueError:
            print("чото не так, вывожу всех друзей")
            max_friends = None

    num_top_nodes_input = input("Количество узлов или 'all': ")
    if num_top_nodes_input.lower() == 'all':
        num_top_nodes = None
    else:
        try:
            num_top_nodes = int(num_top_nodes_input)
        except ValueError:
            print("чото не так, вывожу все узлы")
            num_top_nodes = None

    friends_data, edges, friend_ids = getFriendsInfo(vk, user_id, max_friends=max_friends, delay_between_requests=delay_between_requests)

    total_friends = len(friend_ids)
    total_processed_ids = len({friend['id'] for friend in friends_data})
    total_friends_of_friends = total_processed_ids - total_friends

    G = createSocialGraph(friends_data, edges, user_id)
    plotGraph(G, show_labels=False, num_top_nodes=num_top_nodes, total_friends=total_friends, total_friends_of_friends=total_friends_of_friends)

if __name__ == "__main__":
    main()
