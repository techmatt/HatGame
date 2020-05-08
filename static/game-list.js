
'use strict';

const e = React.createElement;

class GameList extends React.Component {
	constructor(props) {
		super(props);
		this.state = { gameList: ["loading"] };
		this.requestGameList();
	}

	requestGameList() {
		fetch('api/gamelist')
			.then(response => response.json())
			.then(data => {
				console.log("got data %o", data);
				const games = data["games"];
				console.log("got gamelist %o", games);
				this.setState({ gameList: games });
			});
	}

	render() {
		return e(
			'ul',
			null,
			this.state.gameList.map(gameName =>
				e('li', null, gameName))
		);
	}
}

const domContainer = document.querySelector('#game_list_container');
ReactDOM.render(e(GameList), domContainer);
