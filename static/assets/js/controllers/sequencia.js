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
  vm.novaSequencia = { nome: '', acordes: [''] };
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

  vm.adicionarAcorde = function() {
    if (vm.novaSequencia.acordes.length < 32) {
      vm.novaSequencia.acordes.push('');
    }
  };

  vm.removerAcorde = function(indice) {
    if (vm.novaSequencia.acordes.length > 1) {
      vm.novaSequencia.acordes.splice(indice, 1);
    }
  };

  vm.cadastrar = function() {
    vm.erroCadastro = "";
    vm.salvando = true;
    $http.post('sequencias', {
      nome: vm.novaSequencia.nome,
      acordes: vm.novaSequencia.acordes
    })
      .success(function() {
        vm.salvando = false;
        vm.novaSequencia = { nome: '', acordes: [''] };
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
