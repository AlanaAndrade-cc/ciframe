angular.module('deciframeApp').controller('SequenciaController', function($http, $window, ngProgressFactory, $anchorScroll, $location, GENEROS) {
  // paleta fixa por nota raiz; acordes desconhecidos caem na cor default.
  var CORES = {
    'C': '#e6b300',
    'D': '#cb6018',
    'E': '#b72c52',
    'F': '#ba007c',
    'G': '#7b057e',
    'A': '#76aadb',
    'B': '#a3bd31'
  };

  // paleta da tela de acordes; copia local para nao alterar a primeira tela.
  var ACORDES_PALETA = [
    [
      { 'acorde': 'C',  'cor': '#e6b300' },
      { 'acorde': 'C#', 'cor': '#e6b300' },
      { 'acorde': 'Cm', 'cor': '#efcc59' },
      { 'acorde': 'C#m','cor': '#efcc59' },
      { 'acorde': 'C7', 'cor': '#d6a602' },
      { 'acorde': 'C#7','cor': '#d6a602' }
    ],
    [
      { 'acorde': 'D',  'cor': '#cb6018' },
      { 'acorde': 'D#', 'cor': '#cb6018' },
      { 'acorde': 'Dm', 'cor': '#cf6f3e' },
      { 'acorde': 'D#m','cor': '#cf6f3e' },
      { 'acorde': 'D7', 'cor': '#bc5a1d' },
      { 'acorde': 'D#7','cor': '#bc5a1d' }
    ],
    [
      { 'acorde': 'E',  'cor': '#b72c52' },
      { 'acorde': 'Em', 'cor': '#c5516e' },
      { 'acorde': 'E7', 'cor': '#a92f4d' }
    ],
    [
      { 'acorde': 'F',  'cor': '#ba007c' },
      { 'acorde': 'F#', 'cor': '#ba007c' },
      { 'acorde': 'Fm', 'cor': '#c02a88' },
      { 'acorde': 'F#m','cor': '#c02a88' },
      { 'acorde': 'F7', 'cor': '#ad0076' },
      { 'acorde': 'F#7','cor': '#ad0076' }
    ],
    [
      { 'acorde': 'G',  'cor': '#7b057e' },
      { 'acorde': 'G#', 'cor': '#7b057e' },
      { 'acorde': 'Gm', 'cor': '#882888' },
      { 'acorde': 'G#m','cor': '#882888' },
      { 'acorde': 'G7', 'cor': '#710c77' },
      { 'acorde': 'G#7','cor': '#710c77' }
    ],
    [
      { 'acorde': 'A',  'cor': '#76aadb' },
      { 'acorde': 'A#', 'cor': '#76aadb' },
      { 'acorde': 'Am', 'cor': '#89c0e9' },
      { 'acorde': 'A#m','cor': '#89c0e9' },
      { 'acorde': 'A7', 'cor': '#6c9ecc' },
      { 'acorde': 'A#7','cor': '#6c9ecc' }
    ],
    [
      { 'acorde': 'B',  'cor': '#a3bd31' },
      { 'acorde': 'Bm', 'cor': '#cdd54f' },
      { 'acorde': 'B7', 'cor': '#96b02f' }
    ]
  ];

  var corDoAcorde = function(acorde) {
    var raiz = (acorde || '').charAt(0).toUpperCase();
    return CORES[raiz] || '#2E1C74';
  };

  var vm = this;
  vm.sequenciasFamosas = [];
  vm.carregando = true;
  vm.erro = "";
  vm.erroCadastro = "";
  vm.salvando = false;
  vm.minhaSequencia = {};
  vm.isSearching = false;
  vm.showSearchResultsCount = false;
  vm.esfigeSpeech = "";
  vm.musics = [];
  vm.generos = GENEROS;
  vm.meuGenero = "";
  vm.pagina = 1;
  vm.temProxima = false;
  vm.novaSequencia = { nome: '', acordes: [] };
  vm.acordesPaleta = ACORDES_PALETA;
  vm.corDoAcorde = corDoAcorde;
  vm.progressbar = ngProgressFactory.createInstance();

  var mapearSequencia = function(sequencia) {
    return {
      id: sequencia.id,
      nome: sequencia.nome,
      original: sequencia.match_mode === 'tag',
      match_mode: sequencia.match_mode,
      legacy_key: sequencia.legacy_key,
      acordes: (sequencia.acordes || []).map(function(acorde) {
        return { acorde: acorde, cor: corDoAcorde(acorde) };
      })
    };
  };

  var carregarCatalogo = function() {
    vm.carregando = true;
    vm.erro = "";
    $http.get('sequencias')
      .success(function(data) {
        vm.sequenciasFamosas = data.map(mapearSequencia);
        vm.carregando = false;
      })
      .error(function() {
        vm.erro = "Nao foi possivel carregar o catalogo.";
        vm.carregando = false;
      });
  };

  vm.temAcorde = function(acorde) {
    if (vm.minhaSequencia.acordes) {
      return (vm.minhaSequencia.acordes.indexOf(acorde) > -1);
    } else {
      return false;
    }
  }

  var buscar = function() {
    if (!vm.minhaSequencia || vm.minhaSequencia.id === undefined) {
      return;
    }
    vm.progressbar.start();
    vm.esfigeSpeech = "Procurando músicas com base na sequencia...";
    vm.isSearching = true;
    vm.showSearchResultsCount = false;

    var searchString = "similares?sequencia_id=" + vm.minhaSequencia.id +
      "&pagina=" + vm.pagina;
    if (vm.meuGenero !== "" && vm.meuGenero !== null) {
      searchString += "&generos=" + vm.meuGenero;
    }
    $http.get(searchString)
      .success(function(data) {
        vm.progressbar.complete();
        vm.esfigeSpeech = "Encontrei essas músicas";
        vm.isSearching = false;
        vm.showSearchResultsCount = data.length > 0;
        vm.musics = data;
        vm.temProxima = data.length === 100;
      })
      .error(function() {
        vm.progressbar.complete();
        vm.esfigeSpeech = "Ops! Algo errado.";
        vm.isSearching = false;
        vm.showSearchResultsCount = false;
        vm.musics = [];
        vm.temProxima = false;
      });
  };

  vm.pesquisarPorSequencia = function(sequencia) {
    if (sequencia) {
      vm.minhaSequencia = sequencia;
    }
    vm.pagina = 1;
    buscar();
  }

  vm.paginaAnterior = function() {
    if (vm.pagina > 1) {
      vm.pagina -= 1;
      buscar();
    }
  };

  vm.proximaPagina = function() {
    if (vm.temProxima) {
      vm.pagina += 1;
      buscar();
    }
  };

  vm.temAcordeSelecionado = function(acorde) {
    return vm.novaSequencia.acordes.indexOf(acorde) > -1;
  };

  vm.adicionarAcorde = function(acorde) {
    if (acorde && vm.novaSequencia.acordes.length < 32) {
      vm.novaSequencia.acordes.push(acorde);
    }
  };

  vm.removerAcorde = function(indice) {
    if (indice > -1 && indice < vm.novaSequencia.acordes.length) {
      vm.novaSequencia.acordes.splice(indice, 1);
    }
  };

  vm.podeSalvar = function() {
    var nome = (vm.novaSequencia.nome || '').trim();
    return !vm.salvando && nome.length > 0 &&
      vm.novaSequencia.acordes.length > 0;
  };

  vm.cadastrar = function() {
    if (!vm.podeSalvar()) {
      return;
    }
    vm.erroCadastro = "";
    vm.salvando = true;
    $http.post('sequencias', {
      nome: vm.novaSequencia.nome,
      acordes: vm.novaSequencia.acordes
    })
      .success(function() {
        vm.salvando = false;
        vm.novaSequencia = { nome: '', acordes: [] };
        carregarCatalogo();
      })
      .error(function(data, status) {
        vm.salvando = false;
        if (status === 409) {
          vm.erroCadastro = 'Essa sequencia ja esta cadastrada' +
            (data && data.nome ? ' como "' + data.nome + '"' : '') + '.';
        } else if (data && data.erro) {
          vm.erroCadastro = data.erro;
        } else {
          vm.erroCadastro = 'Nao foi possivel cadastrar a sequencia.';
        }
      });
  };

  vm.limparPesquisa = function() {
    vm.minhaSequencia = {};
    vm.musics = [];
    vm.temProxima = false;
  }

  vm.goToLirics = function(music) {
    $window.open(music.url);
  };

  vm.goToResults = function() {
    vm.showSearchResultsCount = false;
    $("body").animate({scrollTop: $("#results").offset().top}, "slow");
  };

  carregarCatalogo();
});
